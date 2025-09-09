from libs.core.aegis import run_quality_gates


def test_aegis_pass():
    run = {
        "docs": {"intro": "x", "usage": "y"},
        "uml": {"classes": []},
        "gantt": {"tasks": [{"id": "A", "dependencies": []}, {"id": "B", "dependencies": ["A"]}]},
        "backlog": {"traceability": {"coverage_pct": 100.0}},
    }
    result = run_quality_gates(run)
    assert result["status"] == "PASSED"
    assert result["errors"] == []


def test_aegis_fail():
    run = {
        "docs": {},
        "uml": {},
        "gantt": {
            "tasks": [{"id": "A", "dependencies": ["B"]}, {"id": "B", "dependencies": ["A"]}]
        },
        "backlog": {"traceability": {"coverage_pct": 90.0}},
    }
    result = run_quality_gates(run)
    assert result["status"] == "FAILED"
    assert any(
        "Docs" in e or "UML" in e or "Gantt" in e or "Backlog" in e for e in result["errors"]
    )
