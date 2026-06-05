from ultralytics import YOLO  # type: ignore
import os
import cv2
import math
import threading

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

model = None
crosswalk_model = None

car_box = None          # last car box – used for plate crop
car_in_crosswalk = 0

# Cached OCR result so it doesn't block the pipeline
_ocr_reader = None
_ocr_lock = threading.Lock()
_ocr_text: str = ""        # latest plate text (updated in background)
_ocr_busy = False          # guard: only one OCR job at a time

# Detection scale – run YOLO on a downscaled frame for speed, draw on full-res
DETECT_SCALE = 0.5         # 50 % of original resolution


def init_models():
    """Load YOLO models once at startup."""
    global model, crosswalk_model, _ocr_reader
    model = YOLO(os.path.join(BASE_DIR, "..", "yolo26n.pt"))
    crosswalk_model = YOLO(os.path.join(BASE_DIR, "best.pt"))
    # Load EasyOCR lazily in background so startup is fast
    threading.Thread(target=_load_ocr, daemon=True).start()


def _load_ocr():
    global _ocr_reader
    import easyocr
    _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)


def _run_ocr_async(crop):
    """Read licence plate text in a background thread (non-blocking)."""
    global _ocr_text, _ocr_busy
    with _ocr_lock:
        if _ocr_busy or _ocr_reader is None:
            return
        _ocr_busy = True

    def _worker():
        global _ocr_text, _ocr_busy
        try:
            results = _ocr_reader.readtext(crop)
            for (_, text, prob) in results:
                if prob > 0.5:
                    _ocr_text = text
        finally:
            _ocr_busy = False

    threading.Thread(target=_worker, daemon=True).start()


def process_frame(frame):
    """
    Run YOLO detection on a single BGR frame.
    • Detects on a downscaled copy for speed.
    • Draws bounding boxes on the original full-res frame.
    • OCR is dispatched asynchronously – never blocks this function.
    Returns the annotated full-res frame.
    """
    global car_box, car_in_crosswalk, _ocr_text

    if frame is None:
        return None

    h, w = frame.shape[:2]
    small = cv2.resize(frame, (int(w * DETECT_SCALE), int(h * DETECT_SCALE)))
    inv = 1.0 / DETECT_SCALE  # scale factor to map boxes back to full-res

    # ── single model.track call for cars AND motorcycles ──────────────────────
    vehicles = model.track(small, classes=[2, 3], verbose=False,
                            tracker="bytetrack.yaml")
    crosswalks = crosswalk_model(small, verbose=False)

    midpoint_x = midpoint_y = 0

    for result in vehicles:
        for box in result.boxes:
            x1, y1, x2, y2 = [int(v * inv) for v in box.xyxy[0]]
            conf = math.ceil(box.conf[0] * 100) / 100
            cls_id = int(box.cls[0]) if box.cls is not None else 2
            label = "Car" if cls_id == 2 else "Motorcycle"
            if conf > 0.5:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(frame, f"{label} {conf:.2f}", (x1, max(y1 - 10, 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (99, 49, 222), 2)
                midpoint_x = (x1 + x2) // 2
                midpoint_y = y2
                car_box = (x1, y1, x2, y2)
                cv2.circle(frame, (midpoint_x, midpoint_y), 6, (0, 0, 255), cv2.FILLED)

    for result in crosswalks:
        for box in result.boxes:
            x1, y1, x2, y2 = [int(v * inv) for v in box.xyxy[0]]
            conf = math.ceil(box.conf[0] * 100) / 100
            if conf > 0.5:
                cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                cv2.putText(frame, f"Crosswalk {conf:.2f}", (x1, max(y1 - 10, 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                if car_box:
                    # Save capture
                    car_in_crosswalk += 1
                    captures_dir = os.path.join(BASE_DIR, "captures")
                    os.makedirs(captures_dir, exist_ok=True)
                    cv2.imwrite(os.path.join(captures_dir, f"car_{car_in_crosswalk}.jpg"), frame)

                    # Dispatch OCR without blocking
                    bx1, by1, bx2, by2 = car_box
                    crop = frame[by1:by2, bx1:bx2]
                    if crop.size > 0:
                        _run_ocr_async(crop.copy())

    # Overlay latest OCR result (if any)
    if _ocr_text and car_box:
        bx1, by1 = car_box[0], car_box[1]
        cv2.putText(frame, _ocr_text, (bx1, max(by1 - 30, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

    return frame
