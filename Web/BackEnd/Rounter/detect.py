import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ML"))

import cv2
import queue
import threading
import time
from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse

import Detector

router = APIRouter(tags=["detection"])

# ── shared state ───────────────────────────────────────────────────────────────
_video_path: str | None = None
_is_running = False

# Two single-slot queues (maxsize=1 → always freshest frame, auto-drops stale)
_raw_q:    queue.Queue = queue.Queue(maxsize=1)   # raw BGR frames
_stream_q: queue.Queue = queue.Queue(maxsize=2)   # JPEG bytes ready to send

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── Thread 1: frame reader ─────────────────────────────────────────────────────
def _reader_thread(video_path: str):
    """
    Reads frames from disk as fast as possible and pushes them into _raw_q.
    Drops any frame already sitting in the queue (keeps it at 1 slot = latest).
    """
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_delay = 1.0 / fps      # honour the video's native frame rate

    if not cap.isOpened():
        return

    while _is_running:
        t0 = time.perf_counter()
        success, frame = cap.read()
        if not success:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)   # loop
            continue

        # Drop stale frame before pushing new one
        try:
            _raw_q.get_nowait()
        except queue.Empty:
            pass
        _raw_q.put(frame)

        # Sleep to match video FPS (avoids hammering the queue)
        elapsed = time.perf_counter() - t0
        time.sleep(max(0.0, frame_delay - elapsed))

    cap.release()


# ── Thread 2: YOLO detector ────────────────────────────────────────────────────
def _detector_thread():
    """
    Pulls raw frames, runs YOLO, encodes to JPEG, pushes into _stream_q.
    Drops stale output so the streamer always gets the freshest result.
    """
    while _is_running:
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

        # Keep queue fresh: drop old frame first
        try:
            _stream_q.get_nowait()
        except queue.Empty:
            pass
        _stream_q.put(data)


# ── MJPEG generator (runs in FastAPI's streaming context) ──────────────────────
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


# ── Endpoints ──────────────────────────────────────────────────────────────────
@router.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    dest = os.path.join(UPLOAD_DIR, "input_video" + ext)
    contents = await file.read()
    with open(dest, "wb") as f:
        f.write(contents)
    global _video_path
    _video_path = dest
    return {"message": "Video uploaded", "path": dest}


@router.post("/start")
async def start_detection():
    global _is_running

    if _video_path is None:
        return {"error": "No video uploaded"}
    if _is_running:
        return {"message": "Already running"}

    Detector.init_models()

    _is_running = True

    # Clear stale data
    for q in (_raw_q, _stream_q):
        while not q.empty():
            try:
                q.get_nowait()
            except queue.Empty:
                break

    threading.Thread(target=_reader_thread,   args=(_video_path,), daemon=True).start()
    threading.Thread(target=_detector_thread, daemon=True).start()

    return {"message": "Detection started"}


@router.post("/stop")
async def stop_detection():
    global _is_running
    _is_running = False
    return {"message": "Detection stopped"}


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


@router.get("/status")
def get_status():
    return {"running": _is_running}
