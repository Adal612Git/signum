from __future__ import annotations

from typing import Any, Dict, List, Tuple


def validate_docs(artifact: Dict[str, Any]) -> Tuple[bool, str]:
    if not artifact:
        return False, "Docs artifact is empty"
    missing: List[str] = []
    for key in ("intro", "usage"):
        if key not in artifact:
            missing.append(key)
    if missing:
        return False, f"Docs missing sections: {', '.join(missing)}"
    return True, "Docs validation passed"


def validate_uml(artifact: Dict[str, Any]) -> Tuple[bool, str]:
    if not artifact:
        return False, "UML artifact is empty"
    if ("classes" not in artifact) and ("relations" not in artifact):
        return False, "UML must contain at least 'classes' or 'relations'"
    return True, "UML validation passed"


def _has_cycle(deps: Dict[str, List[str]]) -> bool:
    # Kahn's algorithm for cycle detection
    nodes = list(deps.keys())
    indeg: Dict[str, int] = {n: 0 for n in nodes}
    adj: Dict[str, List[str]] = {n: [] for n in nodes}

    for n, pres in deps.items():
        for p in pres:
            if p in indeg:
                indeg[n] += 1
                adj[p].append(n)

    queue: List[str] = [n for n, d in indeg.items() if d == 0]
    seen = 0
    i = 0
    while i < len(queue):
        u = queue[i]
        i += 1
        seen += 1
        for v in adj.get(u, []):
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)

    return seen != len(nodes)


def validate_gantt(artifact: Dict[str, Any]) -> Tuple[bool, str]:
    tasks = artifact.get("tasks") if isinstance(artifact, dict) else None
    if not isinstance(tasks, list):
        return False, "Gantt 'tasks' must be a list"

    # Build dependency map id -> [deps]
    deps: Dict[str, List[str]] = {}
    for idx, t in enumerate(tasks):
        if not isinstance(t, dict):
            # Skip invalid task entries
            tid = f"T{idx+1}"
            deps[tid] = []
            continue
        tid = str(t.get("id") or f"T{idx+1}")
        raw = t.get("dependencies")
        if raw is None:
            raw = t.get("depends_on", [])
        if isinstance(raw, list):
            dlist = [str(x) for x in raw]
        else:
            dlist = []
        deps[tid] = dlist

    if _has_cycle(deps):
        return False, "Gantt has cyclic dependencies"
    return True, "Gantt validation passed"


def validate_backlog(artifact: Dict[str, Any]) -> Tuple[bool, str]:
    trace = artifact.get("traceability") if isinstance(artifact, dict) else None
    if not isinstance(trace, dict):
        return False, "Backlog missing 'traceability' section"
    pct = trace.get("coverage_pct")
    if pct is None:
        return False, "Backlog missing 'traceability.coverage_pct'"
    try:
        value = float(pct)
    except (TypeError, ValueError):
        return False, "Backlog 'traceability.coverage_pct' must be a number"
    if value < 95.0:
        return False, f"Backlog coverage {value}% is below 95.0%"
    return True, "Backlog validation passed"


def run_quality_gates(run: Dict[str, Any]) -> Dict[str, Any]:
    """Apply all validators and return status and errors.

    Expected keys in `run`: 'docs', 'uml', 'gantt', 'backlog'.
    Missing sections are treated as empty and will fail their validator.
    """
    errors: List[str] = []

    docs_ok, docs_msg = validate_docs(run.get("docs") or {})
    if not docs_ok:
        errors.append(docs_msg)

    uml_ok, uml_msg = validate_uml(run.get("uml") or {})
    if not uml_ok:
        errors.append(uml_msg)

    gantt_ok, gantt_msg = validate_gantt(run.get("gantt") or {})
    if not gantt_ok:
        errors.append(gantt_msg)

    backlog_ok, backlog_msg = validate_backlog(run.get("backlog") or {})
    if not backlog_ok:
        errors.append(backlog_msg)

    status = "PASSED" if not errors else "FAILED"
    return {"status": status, "errors": errors}
