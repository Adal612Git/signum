from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import dramatiq

from libs.core.aegis import run_quality_gates


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


@dramatiq.actor
def aegis_quality_gates(project_id: str) -> Dict[str, Any]:
    base = Path("artifacts") / project_id

    docs = _read_json(base / "docs" / "docs.json")
    uml = _read_json(base / "uml" / "uml.json")
    gantt = _read_json(base / "plan" / "gantt.json")
    backlog = _read_json(base / "aiona" / "backlog.json")

    result = run_quality_gates(
        {
            "docs": docs,
            "uml": uml,
            "gantt": gantt,
            "backlog": backlog,
        }
    )

    report_dir = base / "aegis"
    _ensure_dir(report_dir)
    report_path = report_dir / "report.json"
    report_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    return result
