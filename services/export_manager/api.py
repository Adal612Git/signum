from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from .github import export_to_github
from .trello import export_to_trello
from .nexus_ops import export_to_nexus_ops
from .pdf import export_to_pdf


router = APIRouter(tags=["exports"])


@router.post("/{kind}")
def create_export(kind: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    project_id = str(payload.get("project_id") or "").strip()
    if not project_id:
        raise HTTPException(status_code=400, detail="Missing project_id")

    kind = kind.lower().replace("-", "_")
    if kind == "trello":
        return export_to_trello(project_id)
    if kind == "github":
        return export_to_github(project_id)
    if kind == "nexus_ops":
        return export_to_nexus_ops(project_id)
    if kind == "pdf":
        return export_to_pdf(project_id)

    raise HTTPException(status_code=404, detail="Unknown export kind")
