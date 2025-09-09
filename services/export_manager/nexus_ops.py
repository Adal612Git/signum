from __future__ import annotations

import json
from typing import Any, Dict

from ._utils import ensure_dir, load_artifacts, artifacts_base, write_export_result


def export_to_nexus_ops(project_id: str) -> Dict[str, Any]:
    """Consolidate available artifacts into a single JSON payload.

    Always writes artifacts/<project_id>/exports/nexus_ops.json using empty dicts
    for any missing inputs.
    """
    try:
        artifacts = load_artifacts(project_id)
        payload: Dict[str, Any] = {
            "project_id": project_id,
            "backlog": artifacts.get("backlog") or {},
            "docs": artifacts.get("docs") or {},
            "uml": artifacts.get("uml") or {},
            "gantt": artifacts.get("gantt") or {},
        }

        base = artifacts_base(project_id) / "exports"
        ensure_dir(base)
        path = base / "nexus_ops.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        result = {"status": "ok", "path": str(path)}
        write_export_result(project_id, "nexus_ops", result)
        return result
    except Exception as e:  # noqa: BLE001
        result = {"status": "failed", "error": str(e)}
        write_export_result(project_id, "nexus_ops", result)
        return result
