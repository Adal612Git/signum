# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    fonts-dejavu-core && \
    rm -rf /var/lib/apt/lists/*

COPY services/orchestrator/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Copy entire repository so Python can import `services` and `libs`
COPY . /app

CMD ["dramatiq", "main", "--processes", "1", "--threads", "2"]
