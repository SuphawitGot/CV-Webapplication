FROM python:3.13-slim

WORKDIR /backend

RUN pip install uv

COPY pyproject.toml uv.lock ./

RUN uv sync

COPY main.py ./

EXPOSE 6767

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "6767"]