import json
from pathlib import Path

import pytest

from libs.core import Artifact, Manifest, ProjectInput, new_manifest, validate_input
from pydantic import ValidationError


def test_validate_input_valid_full():
    data = {
        "name": "Project A",
        "description": "A test project",
        "owner": "alice",
    }
    pi = validate_input(data)
    assert isinstance(pi, ProjectInput)
    assert pi.name == "Project A"
    assert pi.description == "A test project"
    assert pi.owner == "alice"
    # created_at is defaulted
    assert pi.created_at is not None


def test_validate_input_missing_field():
    data = {
        # missing name
        "description": "desc",
        "owner": "bob",
    }
    with pytest.raises(ValidationError):
        validate_input(data)


def test_validate_input_wrong_type_in_nested():
    # Validate Artifact content type must be dict
    with pytest.raises(ValidationError):
        Artifact(id="1", type="file", content=["not", "a", "dict"])  # type: ignore[arg-type]


def test_new_manifest_happy_path():
    arts = [
        Artifact(id="a1", type="file", content={"path": "/tmp/x"}),
        Artifact(id="a2", type="meta", content={"size": 123}),
    ]
    m = new_manifest("proj-x", "1.0.0", arts)
    assert isinstance(m, Manifest)
    assert m.project == "proj-x"
    assert m.version == "1.0.0"
    assert len(m.artifacts) == 2
    assert m.artifacts[0].id == "a1"


def test_schemas_generated_and_valid_shape():
    base = Path(__file__).resolve().parents[1] / "libs" / "core" / "schemas"
    project_schema_path = base / "project_input.schema.json"
    manifest_schema_path = base / "manifest.schema.json"

    assert project_schema_path.is_file()
    assert manifest_schema_path.is_file()

    pj = json.loads(project_schema_path.read_text(encoding="utf-8"))
    mf = json.loads(manifest_schema_path.read_text(encoding="utf-8"))

    # Basic checks for expected properties
    assert pj.get("type") == "object"
    assert "properties" in pj and "name" in pj["properties"] and "owner" in pj["properties"]

    assert mf.get("type") == "object"
    assert "properties" in mf and "artifacts" in mf["properties"]
