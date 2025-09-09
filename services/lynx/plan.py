from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    except Exception:
        return {}


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _default_steps() -> List[Dict[str, Any]]:
    return [
        {
            "step": 1,
            "goal": "Scaffold FastAPI",
            "prompt": "### ⚡ Prompt\n\nCrea un proyecto FastAPI con Poetry. Añade /health.",
            "check": "curl /health → 200",
        },
        {
            "step": 2,
            "goal": "Infraestructura básica",
            "prompt": "### ⚡ Prompt\n\nDefine docker-compose con postgres y redis.",
            "check": "docker compose ps → servicios UP",
        },
        {
            "step": 3,
            "goal": "API Gateway",
            "prompt": "### ⚡ Prompt\n\nImplementa API Gateway con FastAPI y endpoints base.",
            "check": "curl /projects → []",
        },
    ]


def generate_plan(project_id: str) -> Dict[str, Any]:
    """Generate a Codex automation plan from backlog/docs.

    Reads artifacts/<project_id>/backlog.json and artifacts/<project_id>/docs/docs.json if present.
    Always writes automation/codex_plan.json.
    """
    base = Path("artifacts") / project_id
    # Spec path for backlog; also try AIONA path if the spec path is missing
    backlog = _read_json(base / "backlog.json") or _read_json(base / "aiona" / "backlog.json")
    docs = _read_json(base / "docs" / "docs.json")

    steps: List[Dict[str, Any]] = []

    epics = backlog.get("epics") if isinstance(backlog, dict) else None
    if isinstance(epics, list) and epics:
        idx = 1
        for epic in epics:
            title = str(epic.get("title") or epic.get("id") or "Goal")
            user_stories = epic.get("user_stories") or []
            if not isinstance(user_stories, list):
                user_stories = []
            for us in user_stories:
                benefit = str(us.get("benefit") or us.get("id") or "User Story")
                tasks = us.get("tasks") or []
                if not isinstance(tasks, list) or not tasks:
                    # Create a single step for the USR
                    steps.append(
                        {
                            "step": idx,
                            "goal": title,
                            "prompt": f"### ⚡ Prompt\n\n{benefit}",
                            "check": f"USR completada: {benefit}",
                        }
                    )
                    idx += 1
                    continue
                for t in tasks:
                    tname = str(t.get("name") or t.get("id") or "Task")
                    prompt = f"### ⚡ Prompt\n\n{benefit}\n\n- Task: {tname}"
                    steps.append(
                        {
                            "step": idx,
                            "goal": title,
                            "prompt": prompt,
                            "check": f"Tarea '{tname}' implementada y validada",
                        }
                    )
                    idx += 1

    if not steps:
        steps = _default_steps()

    # Build output
    plan: Dict[str, Any] = {
        "project_id": project_id,
        "steps": steps,
        "context": {
            "docs_present": bool(docs),
            "backlog_present": bool(backlog),
        },
    }

    out_dir = Path("automation")
    _ensure_dir(out_dir)
    out_path = out_dir / "codex_plan.json"
    out_path.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {"status": "ok", "path": str(out_path), "steps": len(steps)}
