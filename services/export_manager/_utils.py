from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}


def artifacts_base(project_id: str) -> Path:
    return Path("artifacts") / project_id


def load_artifacts(project_id: str) -> Dict[str, Any]:
    base = artifacts_base(project_id)
    backlog = read_json(base / "aiona" / "backlog.json")
    if not backlog:
        backlog = read_json(base / "backlog.json")
    docs = read_json(base / "docs" / "docs.json")
    uml = read_json(base / "uml" / "uml.json")
    gantt = read_json(base / "plan" / "gantt.json")
    return {"backlog": backlog, "docs": docs, "uml": uml, "gantt": gantt}


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def env(name: str) -> Optional[str]:
    v = os.getenv(name)
    return v.strip() if isinstance(v, str) and v.strip() else None


def b64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def write_export_result(project_id: str, kind: str, result: Dict[str, Any]) -> Path:
    base = artifacts_base(project_id) / "exports"
    ensure_dir(base)
    path = base / f"{kind}.result.json"
    path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path
