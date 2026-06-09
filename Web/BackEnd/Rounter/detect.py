import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ML"))

import cv2
import queue
import threading
import time
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import Detector

router = APIRouter(tags=["detection"])

# ── shared state ───────────────────────────────────────────────────────────────
_video_path: str | None = None
_is_running = False
_is_paused  = False

# Two single-slot queues (maxsize=1 → always freshest frame, auto-drops stale)
_raw_q:    queue.Queue = queue.Queue(maxsize=1)   # raw BGR frames
_stream_q: queue.Queue = queue.Queue(maxsize=2)   # JPEG bytes ready to send

UPLOAD_DIR  = os.path.join(os.path.dirname(__file__), "..", "uploads")
CAPTURE_DIR = os.path.join(os.path.dirname(__file__), "..", "captures")
os.makedirs(UPLOAD_DIR,  exist_ok=True)
os.makedirs(CAPTURE_DIR, exist_ok=True)


# ── Thread 1: frame reader ─────────────────────────────────────────────────────
def _reader_thread(video_path: str):
    """
    Reads frames from disk as fast as possible and pushes them into _raw_q.
    Honours _is_paused by skipping pushes while paused.
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_delay = 1.0 / fps

    if not cap.isOpened():
        return

    while _is_running:
        if _is_paused:
            time.sleep(0.05)
            continue

        t0 = time.perf_counter() # .perf_counter is time stamp 
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)   # loop
            continue

        try:
            _raw_q.get_nowait()  # get_nowait() is use to get the frame from queue
        except queue.Empty:
            pass
        _raw_q.put(frame)

        elapsed = time.perf_counter() - t0
        time.sleep(max(0.0, frame_delay - elapsed))

    cap.release()


# ── Thread 2: YOLO detector ────────────────────────────────────────────────────
def _detector_thread():
    """
    Pulls raw frames, runs YOLO + crosswalk logic, encodes to JPEG, pushes into _stream_q.
    """
    while _is_running:
        if _is_paused:
            time.sleep(0.05)
            continue

        try:
            frame = _raw_q.get(timeout=0.1)
        except queue.Empty:
            continue

        annotated = Detector.process_frame(frame)
        if annotated is None:
            continue

        ret, jpeg = cv2.imencode(".jpg", annotated,
                                 [cv2.IMWRITE_JPEG_QUALITY, 75])
        if not ret:
            continue

        data = jpeg.tobytes()

        try:
            _stream_q.get_nowait()
        except queue.Empty:
            pass
        _stream_q.put(data)


# ── MJPEG generator ────────────────────────────────────────────────────────────
def _frame_generator():
    """Yield MJPEG frames as fast as they are ready."""
    while True:
        try:
            jpeg_bytes = _stream_q.get(timeout=0.2)
        except queue.Empty:
            if not _is_running:
                break
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + jpeg_bytes + b"\r\n"
        )


def _do_start():
    """Internal helper: initialise models and spawn worker threads."""
    global _is_running, _is_paused
    Detector.init_models()
    _is_running = True
    _is_paused  = False

    for q in (_raw_q, _stream_q):
        while not q.empty():
            try:
                q.get_nowait()
            except queue.Empty:
                break

    threading.Thread(target=_reader_thread,   args=(_video_path,), daemon=True).start()
    threading.Thread(target=_detector_thread, daemon=True).start()


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload a video and immediately start detection."""
    global _video_path, _is_running, _is_paused

    # Stop any currently running detection
    if _is_running:
        _is_running = False
        _is_paused  = False
        time.sleep(0.3)   # let threads wind down

    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    dest = os.path.join(UPLOAD_DIR, "input_video" + ext)
    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)
    _video_path = dest

    # Auto-start detection immediately
    _do_start()

    return {"message": "Video uploaded and detection started", "path": dest}


@router.post("/start")
async def start_detection():
    global _is_running

    if _video_path is None:
        return {"error": "No video uploaded"}
    if _is_running:
        return {"message": "Already running"}

    _do_start()
    return {"message": "Detection started"}


@router.post("/stop")
async def stop_detection():
    global _is_running, _is_paused
    _is_running = False
    _is_paused  = False
    return {"message": "Detection stopped"}


@router.post("/pause")
async def pause_detection():
    global _is_paused
    if not _is_running:
        return {"error": "Detection is not running"}
    _is_paused = True
    return {"message": "Detection paused"}


@router.post("/resume")
async def resume_detection():
    global _is_paused
    if not _is_running:
        return {"error": "Detection is not running"}
    _is_paused = False
    return {"message": "Detection resumed"}


@router.get("/stream")
def stream_video():
    return StreamingResponse(
        _frame_generator(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
        },
    )


@router.get("/violations")
def get_violations():
    """Return all auto-captured violation records (id, filename, plate, timestamp)."""
    return {"violations": Detector.get_violations()}


@router.get("/status")
def get_status():
    return {"running": _is_running, "paused": _is_paused}
