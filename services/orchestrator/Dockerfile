# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY services/orchestrator/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY services/orchestrator /app
# Include shared libs for imports
COPY libs /app/libs

CMD ["dramatiq", "main", "--processes", "1", "--threads", "2"]
