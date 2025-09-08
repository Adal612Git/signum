# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

# System deps for building and curl for health checks if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY services/api-gateway/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

# Copy application code
COPY services/api-gateway /app
# Also copy shared libs so we can import libs.core
COPY libs /app/libs

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

