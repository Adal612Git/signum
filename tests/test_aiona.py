from libs.aiona import build_aiona
import json
from pathlib import Path


def test_build_aiona(tmp_path):
    proj = {"id": "pytest-aiona", "goals": ["Automatizar despliegue", "Mejorar logs de auditoría"]}
    out = build_aiona(proj)
    backlog_file = Path(out["backlog.json"])
    data = json.loads(backlog_file.read_text())

    assert data["pipeline_stage"] == "AIONA"
    assert data["traceability"]["coverage_pct"] >= 95.0
    assert len(data["epics"]) == 2
    for epic in data["epics"]:
        assert "dor" in epic
        assert "dod" in epic
        assert len(epic["user_stories"]) >= 1
