from __future__ import annotations

import os
import logging
from uuid import uuid4
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from dotenv import load_dotenv
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError

from libs.core import ProjectInput, Manifest
import dramatiq
from dramatiq.brokers.redis import RedisBroker
from services.orchestrator.main import process_project


# Load .env if present (useful for local runs). In containers, env is provided by compose.
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("api-gateway")

app = FastAPI(title="Signum API Gateway", version="0.1.0")

# Dramatiq broker to Redis (shared with orchestrator)
redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
broker = RedisBroker(url=redis_url)
dramatiq.set_broker(broker)


def _minio_client():
    endpoint = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
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
        config=BotoConfig(signature_version="s3v4"),
    )


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/projects", status_code=202)
def create_project(payload: Dict[str, Any]) -> JSONResponse:
    # Validate manually to return 400 on invalid input (instead of 422)
    try:
        pi = ProjectInput.model_validate(payload)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    run_id = str(uuid4())

    # Enqueue task to orchestrator via actor
    # Use JSON mode to ensure datetime is serialized for Dramatiq encoder
    process_project.send(run_id, pi.model_dump(mode="json"))

    logger.info("Project %s enqueued", run_id)

    return JSONResponse(status_code=202, content={"run_id": run_id})


@app.get("/projects/{project_id}")
def get_project(project_id: str) -> Dict[str, Any]:
    # Stub status and partial manifest
    manifest = Manifest(project=project_id, version="0.0.1", artifacts=[])
    return {"status": "pending", "manifest": manifest.model_dump()}


@app.get("/artifacts/{artifact_id}/{path:path}")
def get_artifact(artifact_id: str, path: str = ""):
    # artifact keys are stored as <artifact_id>/<path>
    s3 = _minio_client()
    key = f"{artifact_id}/{path}" if path else artifact_id
    bucket = "artifacts"
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        code = e.response.get("Error", {}).get("Code")
        if code in {"NoSuchKey", "404"}:
            raise HTTPException(status_code=404, detail="Artifact not found")
        raise

    body = obj["Body"]  # botocore.response.StreamingBody
    content_type = obj.get("ContentType", "application/octet-stream")
    filename = os.path.basename(path) if path else artifact_id
    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(body, media_type=content_type, headers=headers)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
