# ── Backend Dockerfile ─────────────────────────────────────────────
# Multi-stage build for the FastAPI + YOLO + EasyOCR backend

FROM python:3.13-slim AS backend

WORKDIR /app

# Install system dependencies required by OpenCV, EasyOCR, and video processing
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency resolution
RUN pip install --no-cache-dir uv

# Copy dependency file first (Docker layer caching — only re-installs when deps change)
COPY pyproject.toml .

# Install Python dependencies
# Note: Using CPU-only PyTorch in Docker to keep image size smaller.
# If you need GPU support, use the nvidia/cuda base image instead.
RUN uv pip install --system --no-cache \
    --extra-index-url https://download.pytorch.org/whl/cpu \
    torch torchvision \
    && uv pip install --system --no-cache -r pyproject.toml \
    --override /dev/null 2>/dev/null || uv pip install --system --no-cache -r pyproject.toml

# Copy the entire backend source code
COPY . .

# Create directories for uploads and captures
RUN mkdir -p /app/uploads /app/captures /app/ML/captures

# Expose the FastAPI port
EXPOSE 8000

# Start the FastAPI server
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]