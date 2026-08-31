FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 시스템 패키지
RUN apt-get update \
    && apt-get install -y \
        gcc \
        g++ \
        libgl1 \
        libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install --no-cache-dir uv

# dependency 파일 먼저 복사
COPY pyproject.toml uv.lock* ./

# dependency 설치
RUN uv sync --frozen --no-dev

# backend 전체 복사
COPY . .

EXPOSE 8000

CMD [
    "uv",
    "run",
    "uvicorn",
    "main:app",
    "--host",
    "0.0.0.0",
    "--port",
    "8000"
]