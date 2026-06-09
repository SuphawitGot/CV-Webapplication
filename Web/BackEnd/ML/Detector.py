from ultralytics import YOLO  # type: ignore
import os
import sys
import cv2
import math
import threading
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Add parent directory to path so we can import database & model
sys.path.insert(0, os.path.join(BASE_DIR, ".."))
from database import SessionLocal
from model import Violation

model = None
crosswalk_model = None

# Cached OCR result so it doesn't block the pipeline
_ocr_reader = None
_ocr_lock = threading.Lock()
_ocr_busy = False

# Detection scale – run YOLO on a downscaled frame for speed, draw on full-res
DETECT_SCALE = 0.5

# ── Violation log (thread-safe) ───────────────────────────────────────────────
# Each entry: {"id": int, "filename": str, "plate": str, "timestamp": str}
_violations: list[dict] = []
_violations_lock = threading.Lock()

# Cooldown: after a crossing event, ignore new triggers for N seconds
_last_capture_time: float = 0.0
CAPTURE_COOLDOWN = 3.0       # seconds between captures for same/different car


def init_models():
    """Load YOLO models once at startup."""
    global model, crosswalk_model, _ocr_reader, _violations, _last_capture_time
    model = YOLO(os.path.join(BASE_DIR, "..", "yolo26n.pt"))
    crosswalk_model = YOLO(os.path.join(BASE_DIR, "best.pt"))
    _violations = []
    _last_capture_time = 0.0
    # Load EasyOCR lazily in background so startup is fast
    threading.Thread(target=_load_ocr, daemon=True).start()


def _load_ocr():
    global _ocr_reader
    import easyocr
    _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)


def _run_ocr_and_log(crop, filename: str, violation_id: int):
    """Read licence plate text in a background thread, then update the violation log."""
    global _ocr_busy

    with _ocr_lock:
        if _ocr_busy or _ocr_reader is None:
            return
        _ocr_busy = True

    def _worker():
        global _ocr_busy
        plate_text = ""
        try:
            results = _ocr_reader.readtext(crop)
            best_prob = 0.0
            for (_, text, prob) in results:
                if prob > best_prob:
                    best_prob = prob
                    plate_text = text
            if best_prob < 0.3:
                plate_text = ""
        finally:
            _ocr_busy = False

        final_plate = plate_text.upper() if plate_text else "—"

        # Update in-memory violation entry
        with _violations_lock:
            for v in _violations:
                if v["id"] == violation_id:
                    v["plate"] = final_plate
                    break

        # ── Save to PostgreSQL ────────────────────────────────────────────
        db = SessionLocal()
        try:
            violation = Violation(
                plate=final_plate,
                filename=filename,
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            )
            db.add(violation)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"[Detector] DB save error: {e}")
        finally:
            db.close()

    threading.Thread(target=_worker, daemon=True).start()


def get_violations() -> list[dict]:
    """Return a snapshot of all violations so far."""
    with _violations_lock:
        return list(_violations)


def process_frame(frame):
    """
    Run YOLO detection on a single BGR frame.
    • Detects on a downscaled copy for speed.
    • Draws bounding boxes + crosswalk boxes on the original full-res frame.
    • When a vehicle midpoint enters the crosswalk region, auto-captures and OCRs (with cooldown).
    Returns the annotated full-res frame.
    """
    global _last_capture_time

    if frame is None:
        return None

    h, w = frame.shape[:2]
    small = cv2.resize(frame, (int(w * DETECT_SCALE), int(h * DETECT_SCALE)))
    inv = 1.0 / DETECT_SCALE

    # ── Detect crosswalks ─────────────────────────────────────────────────────
    crosswalk_results = crosswalk_model(small, verbose=False)
    crosswalk_boxes = []   # list of (x1,y1,x2,y2) in full-res coords

    for result in crosswalk_results:
        for box in result.boxes:
            conf = math.ceil(box.conf[0] * 100) / 100
            if conf > 0.5:
                x1, y1, x2, y2 = [int(v * inv) for v in box.xyxy[0]]
                crosswalk_boxes.append((x1, y1, x2, y2))
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 160, 0), 2)
                cv2.putText(frame, f"Crosswalk {conf:.2f}", (x1, max(y1 - 10, 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 160, 0), 2)

    # ── Detect & track vehicles ───────────────────────────────────────────────
    vehicles = model.track(small, classes=[2, 3], verbose=False,
                           tracker="bytetrack.yaml")

    now = time.perf_counter()

    for result in vehicles:
        for box in result.boxes:
            x1, y1, x2, y2 = [int(v * inv) for v in box.xyxy[0]]
            conf = math.ceil(box.conf[0] * 100) / 100
            cls_id = int(box.cls[0]) if box.cls is not None else 2
            label = "Car" if cls_id == 2 else "Motorcycle"

            if conf < 0.5:
                continue

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, f"{label} {conf:.2f}", (x1, max(y1 - 10, 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (99, 49, 222), 2)

            # Midpoint: horizontal centre, vertical bottom of bounding box
            mid_x = (x1 + x2) // 2
            mid_y = y2
            cv2.circle(frame, (mid_x, mid_y), 6, (0, 0, 255), cv2.FILLED)

            # ── Check if midpoint is inside any crosswalk box ─────────────
            in_crosswalk = any(
                cx1 <= mid_x <= cx2 and cy1 <= mid_y <= cy2
                for (cx1, cy1, cx2, cy2) in crosswalk_boxes
            )

            if in_crosswalk and (now - _last_capture_time) > CAPTURE_COOLDOWN:
                _last_capture_time = now

                # Save capture
                captures_dir = os.path.join(BASE_DIR, "captures")
                os.makedirs(captures_dir, exist_ok=True)
                ts = time.strftime("%Y-%m-%d %H:%M:%S")
                filename = f"capture_{int(time.time() * 1000)}.jpg"
                filepath = os.path.join(captures_dir, filename)
                cv2.imwrite(filepath, frame)

                # Add violation entry (plate filled in once OCR finishes)
                with _violations_lock:
                    vid = len(_violations) + 1
                    _violations.append({
                        "id":        vid,
                        "filename":  filename,
                        "plate":     "Reading…",
                        "timestamp": ts,
                    })

                # Dispatch OCR on the car crop
                crop = frame[y1:y2, x1:x2]
                if crop.size > 0:
                    _run_ocr_and_log(crop.copy(), filename, vid)

                # Draw red alert flash on frame
                cv2.putText(frame, "! VIOLATION CAPTURED !", (10, h - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 3)

    # ── Overlay violations count ──────────────────────────────────────────────
    with _violations_lock:
        count = len(_violations)
        latest_plate = _violations[-1]["plate"] if _violations else ""

    if count > 0:
        cv2.putText(frame, f"Violations: {count}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
    if latest_plate and latest_plate not in ("Reading…", "—"):
        cv2.putText(frame, f"Plate: {latest_plate}", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    return frame
