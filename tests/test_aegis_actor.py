from __future__ import annotations

import json
import sys
import types
from pathlib import Path


def _mock_dramatiq_module() -> None:
    mod = types.ModuleType("dramatiq")

    class DummyActor:
        def __init__(self, fn):
            self.fn = fn

        def __call__(self, *args, **kwargs):
            # Simulate async call interface; not used in tests
            return {"message": "dummy"}

        def send(self, *args, **kwargs):
            # No-op for tests
            return None

    def actor(fn=None, **_kwargs):
        def deco(f):
            return DummyActor(f)

        return deco(fn) if fn is not None else deco

    mod.actor = actor  # type: ignore[attr-defined]
    sys.modules["dramatiq"] = mod


def _import_actor():
    # Ensure our dummy dramatiq is in place before importing the actor
    _mock_dramatiq_module()
    from services.orchestrator.actors.aegis import aegis_quality_gates

    return aegis_quality_gates


def test_aegis_passed(tmp_path: Path):
    aegis_quality_gates = _import_actor()

    project_id = "proj-pass"
    base = tmp_path / "artifacts" / project_id
    (base / "docs").mkdir(parents=True)
    (base / "uml").mkdir(parents=True)
    (base / "plan").mkdir(parents=True)
    (base / "aiona").mkdir(parents=True)

    (base / "docs" / "docs.json").write_text(
        json.dumps({"intro": "x", "usage": "y"}), encoding="utf-8"
    )
    (base / "uml" / "uml.json").write_text(json.dumps({"classes": []}), encoding="utf-8")
    gantt_ok = {"tasks": [{"id": "A", "dependencies": []}, {"id": "B", "dependencies": ["A"]}]}
    (base / "plan" / "gantt.json").write_text(json.dumps(gantt_ok), encoding="utf-8")
    (base / "aiona" / "backlog.json").write_text(
        json.dumps({"traceability": {"coverage_pct": 100.0}}), encoding="utf-8"
    )

    # Run inside tmp cwd so actor reads the simulated artifacts/
    cwd = Path.cwd()
    try:
        sys.path.insert(0, str(tmp_path))
        # chdir for relative artifacts path
        import os

        os.chdir(tmp_path)
        result = aegis_quality_gates.fn(project_id)  # type: ignore[attr-defined]
    finally:
        os.chdir(cwd)
        if sys.path and sys.path[0] == str(tmp_path):
            sys.path.pop(0)

    assert result == {"status": "PASSED", "errors": []}

    report = json.loads((base / "aegis" / "report.json").read_text(encoding="utf-8"))
    assert report == result


def test_aegis_failed(tmp_path: Path):
    aegis_quality_gates = _import_actor()

    project_id = "proj-fail"
    base = tmp_path / "artifacts" / project_id
    (base / "docs").mkdir(parents=True)
    (base / "uml").mkdir(parents=True)
    (base / "plan").mkdir(parents=True)
    (base / "aiona").mkdir(parents=True)

    # Empty docs and UML
    (base / "docs" / "docs.json").write_text(json.dumps({}), encoding="utf-8")
    (base / "uml" / "uml.json").write_text(json.dumps({}), encoding="utf-8")

    # Cyclic Gantt A <-> B
    gantt_bad = {"tasks": [{"id": "A", "dependencies": ["B"]}, {"id": "B", "dependencies": ["A"]}]}
    (base / "plan" / "gantt.json").write_text(json.dumps(gantt_bad), encoding="utf-8")

    # Backlog coverage below 95
    (base / "aiona" / "backlog.json").write_text(
        json.dumps({"traceability": {"coverage_pct": 90.0}}), encoding="utf-8"
    )

    cwd = Path.cwd()
    try:
        sys.path.insert(0, str(tmp_path))
        import os

        os.chdir(tmp_path)
        result = aegis_quality_gates.fn(project_id)  # type: ignore[attr-defined]
    finally:
        os.chdir(cwd)
        if sys.path and sys.path[0] == str(tmp_path):
            sys.path.pop(0)

    assert isinstance(result, dict)
    assert result.get("status") == "FAILED"
    assert isinstance(result.get("errors"), list) and len(result["errors"]) >= 3

    report = json.loads((base / "aegis" / "report.json").read_text(encoding="utf-8"))
    assert report == result
