FROM python:3.13-slim

WORKDIR /app

# system dependencies for opencv and easyocr
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .


RUN pip install uv
RUN uv pip install --system -r pyproject.toml

COPY . .

EXPOSE 8000
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]