from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict

import dramatiq
from dramatiq.brokers.redis import RedisBroker
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError

from libs.core import ProjectInput, new_manifest


load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")


def _minio_client():
    endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
    access_key = os.getenv("MINIO_ROOT_USER")
    secret_key = os.getenv("MINIO_ROOT_PASSWORD")
    if not access_key or not secret_key:
        raise RuntimeError("Missing MINIO credentials in environment variables.")
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name="us-east-1",
    )


def _ensure_bucket(s3, bucket: str) -> None:
    try:
        s3.head_bucket(Bucket=bucket)
    except ClientError:
        # Try to create if missing
        try:
            s3.create_bucket(Bucket=bucket)
        except ClientError as e:
            # Might be due to already owned or race condition
            logger.warning("create_bucket failed: %s", e)


# Configure Redis broker from env
redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
broker = RedisBroker(url=redis_url)
dramatiq.set_broker(broker)


@dramatiq.actor
def process_project(run_id: str, data: Dict[str, Any]) -> None:
    """Validate input and write a partial manifest to MinIO."""
    logger.info("Processing project %s", run_id)
    try:
        # Validate input using shared schema
        _ = ProjectInput.model_validate(data)

        # Build a partial manifest (empty artifacts for now)
        manifest = new_manifest(project_name=data["name"], version="0.0.1", artifacts=[])

        s3 = _minio_client()
        bucket = "artifacts"
        _ensure_bucket(s3, bucket)

        key = f"{run_id}/manifest.json"
        body = json.dumps(manifest.model_dump(), ensure_ascii=False).encode("utf-8")
        s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType="application/json")

        logger.info("Manifest stored at s3://%s/%s", bucket, key)
    except Exception as e:
        logger.exception("Failed processing run_id=%s: %s", run_id, e)
        raise


if __name__ == "__main__":
    # Local manual enqueue example (for quick sanity checks)
    sample = {"name": "demo", "description": "d", "owner": "you"}
    process_project.send("local-run-id", sample)
