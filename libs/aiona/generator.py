from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


@dataclass
class Goal:
    id: str
    text: str


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _normalize_goals(raw: Any) -> List[Goal]:
    goals: List[Goal] = []
    if not raw:
        return goals
    if isinstance(raw, list):
        for i, g in enumerate(raw, start=1):
            if isinstance(g, str):
                goals.append(Goal(id=f"G{i}", text=g.strip()))
            elif isinstance(g, dict):
                gid = str(g.get("id") or f"G{i}")
                txt = str(g.get("text") or g.get("goal") or g.get("name") or gid)
                goals.append(Goal(id=gid, text=txt.strip()))
    return goals


def _default_dor(level: str) -> List[str]:
    common = [
        "Objetivo comprendido por el equipo",
        "Stakeholders identificados",
    ]
    if level == "epic":
        return common + [
            "Criterios de éxito del EPIC definidos",
            "Alcance inicial y riesgos mapeados",
        ]
    if level == "usr":
        return common + [
            "Actor y beneficio definidos",
            "Criterios de aceptación preliminares",
        ]
    # task
    return common + [
        "Dependencias identificadas",
        "Estimación preliminar",
    ]


def _default_dod(level: str) -> List[str]:
    if level == "epic":
        return [
            "Todas las USR del EPIC completadas",
            "Métricas de valor verificadas",
        ]
    if level == "usr":
        return [
            "Criterios de aceptación verificados",
            "Documentación de usuario actualizada",
        ]
    # task
    return [
        "Implementación revisada (code review)",
        "Pruebas pasan en CI",
        "Checklist de seguridad aplicado",
    ]


def _guess_actor(goal_text: str) -> str:
    low = goal_text.lower()
    if "admin" in low:
        return "admin"
    if "dev" in low or "developer" in low:
        return "developer"
    if "ops" in low or "operaciones" in low:
        return "ops"
    return "user"


def build_aiona(project: Dict[str, Any]) -> Dict[str, str]:
    """
    Transforma una lista de goals en un backlog jerárquico EPIC→USR→TASK con DoR/DoD y
    trazabilidad, y lo guarda como backlog.json.

    Entrada esperada en `project["goals"]`: lista de str o dicts con {id?, text?/goal?/name?}.
    Salida: artifacts/<project_id>/aiona/backlog.json
    """
    proj_id = str(project.get("id") or project.get("run_id") or project.get("name") or "project")
    out_dir = Path("artifacts") / proj_id / "aiona"
    _ensure_dir(out_dir)

    raw_goals = project.get("goals") or []
    goals = _normalize_goals(raw_goals)

    epics: List[Dict[str, Any]] = []
    covered: set[str] = set()

    for i, g in enumerate(goals, start=1):
        epic_id = f"E{i}"
        usr_id = f"U{i}"
        t1_id = f"T{i}-1"
        t2_id = f"T{i}-2"
        t3_id = f"T{i}-3"

        # Build tasks (simple linear dependency chain to satisfy dependency requirement)
        tasks = [
            {
                "id": t1_id,
                "name": "Clarificar criterios de aceptación",
                "depends_on": [],
                "dor": _default_dor("task"),
                "dod": _default_dod("task"),
                "goal_refs": [g.id],
            },
            {
                "id": t2_id,
                "name": "Implementar funcionalidad",
                "depends_on": [t1_id],
                "dor": _default_dor("task"),
                "dod": _default_dod("task"),
                "goal_refs": [g.id],
            },
            {
                "id": t3_id,
                "name": "Probar y documentar",
                "depends_on": [t2_id],
                "dor": _default_dor("task"),
                "dod": _default_dod("task"),
                "goal_refs": [g.id],
            },
        ]

        usr = {
            "id": usr_id,
            "epic_id": epic_id,
            "actor": _guess_actor(g.text),
            "benefit": g.text,
            "dor": _default_dor("usr"),
            "dod": _default_dod("usr"),
            "goal_refs": [g.id],
            "tasks": tasks,
        }

        epic = {
            "id": epic_id,
            "title": g.text,
            "description": f"EPIC derivado del goal {g.id}",
            "dor": _default_dor("epic"),
            "dod": _default_dod("epic"),
            "goal_refs": [g.id],
            "user_stories": [usr],
        }

        epics.append(epic)
        covered.add(g.id)

    total_goals = len(goals)
    covered_goals = len(covered)
    coverage_pct = round(100.0 * covered_goals / total_goals, 2) if total_goals else 0.0

    root: Dict[str, Any] = {
        "pipeline_stage": "AIONA",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project_id": proj_id,
        "goals_count": total_goals,
        "epics": epics,
        "traceability": {
            "total_goals": total_goals,
            "covered_goals": covered_goals,
            "coverage_pct": coverage_pct,
        },
    }

    # Ensure ≥95% goal traceability
    # Our generation maps 1:1 goal→epic so coverage is typically 100% if goals present.
    # If not, the % will reflect it in the JSON.

    backlog_path = out_dir / "backlog.json"
    backlog_path.write_text(json.dumps(root, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "backlog.json": str(backlog_path),
        "base_dir": str(out_dir),
    }
