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


@dramatiq.actor
def docs_build(project: Dict[str, Any]) -> None:
    """Builds documentation and uploads to MinIO under artifacts/<id>/docs/."""
    proj_id = str(project.get("id") or project.get("run_id") or project.get("name") or "project")
    logger.info("Building docs for %s", proj_id)
    try:
        # Lazy import to avoid hard dependency in importers (e.g., api-gateway)
        from libs.docgen import build_docs  # type: ignore

        # Generate docs locally
        outputs = build_docs(project)

        # Upload to MinIO
        s3 = _minio_client()
        bucket = "artifacts"
        _ensure_bucket(s3, bucket)

        base_prefix = f"{proj_id}/docs/"
        for name, path in outputs.items():
            key = base_prefix + os.path.basename(path)
            with open(path, "rb") as f:
                body = f.read()
            content_type = (
                "application/pdf"
                if name.endswith(".pdf")
                else ("text/markdown" if name.endswith(".md") else "text/html")
            )
            s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)
        logger.info("Docs generated for %s at artifacts/%sdocs/", proj_id, proj_id + "/")
    except Exception as e:
        logger.exception("Failed docs generation for %s: %s", proj_id, e)
        raise


@dramatiq.actor
def uml_build(project: Dict[str, Any]) -> None:
    """Builds UML artifacts and uploads to MinIO under artifacts/<id>/uml/."""
    proj_id = str(project.get("id") or project.get("run_id") or project.get("name") or "project")
    try:
        from libs.uml import build_uml  # type: ignore

        outputs = build_uml(project)

        s3 = _minio_client()
        bucket = "artifacts"
        _ensure_bucket(s3, bucket)

        base_prefix = f"{proj_id}/uml/"
        for name, path in outputs.items():
            if name == "base_dir":
                continue
            filename = os.path.basename(path)
            key = base_prefix + filename
            with open(path, "rb") as f:
                body = f.read()
            content_type = "text/markdown" if filename.endswith(".md") else "application/json"
            s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)
            logger.info("Uploaded UML %s to s3://%s/%s", filename, bucket, key)

        logger.info("UML generated for %s at artifacts/%suml/", proj_id, proj_id + "/")
    except Exception as e:
        logger.exception("Failed UML generation for %s: %s", proj_id, e)
        raise


@dramatiq.actor
def gantt_build(project: Dict[str, Any]) -> None:
    """Builds Gantt artifacts and uploads to MinIO under artifacts/<id>/plan/."""
    proj_id = str(project.get("id") or project.get("run_id") or project.get("name") or "project")
    try:
        from libs.gantt import build_gantt  # type: ignore

        outputs = build_gantt(project)

        s3 = _minio_client()
        bucket = "artifacts"
        _ensure_bucket(s3, bucket)

        base_prefix = f"{proj_id}/plan/"
        for name, path in outputs.items():
            if name == "base_dir":
                continue
            filename = os.path.basename(path)
            key = base_prefix + filename
            with open(path, "rb") as f:
                body = f.read()
            if filename.endswith(".json"):
                content_type = "application/json"
            elif filename.endswith(".png"):
                content_type = "image/png"
            else:
                content_type = "text/plain"
            s3.put_object(Bucket=bucket, Key=key, Body=body, ContentType=content_type)
            logger.info("Uploaded Gantt %s to s3://%s/%s", filename, bucket, key)

        logger.info("Gantt generated for %s at artifacts/%splan/", proj_id, proj_id + "/")
    except Exception as e:
        logger.exception("Failed Gantt generation for %s: %s", proj_id, e)
        raise


if __name__ == "__main__":
    # Local manual enqueue example (for quick sanity checks)
    sample = {"name": "demo", "description": "d", "owner": "you"}
    process_project.send("local-run-id", sample)
