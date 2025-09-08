from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Artifact(BaseModel):
    id: str
    type: str
    content: Dict[str, Any]


class ProjectInput(BaseModel):
    name: str
    description: str
    owner: str
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)


class Manifest(BaseModel):
    project: str
    version: str
    artifacts: List[Artifact]


def validate_input(data: Dict[str, Any]) -> ProjectInput:
    """Validate input dict into a ProjectInput instance using Pydantic v2 API."""
    return ProjectInput.model_validate(data)


def new_manifest(project_name: str, version: str, artifacts: List[Artifact]) -> Manifest:
    """Create a new Manifest instance from parts."""
    return Manifest(project=project_name, version=version, artifacts=artifacts)


def _generate_json_schemas() -> None:
    """Generate JSON schema files for the models under libs/core/schemas/.

    Files:
    - project_input.schema.json
    - manifest.schema.json
    """
    import json
    from pathlib import Path

    base = Path(__file__).resolve().parent
    schemas_dir = base / "schemas"
    schemas_dir.mkdir(parents=True, exist_ok=True)

    project_schema_path = schemas_dir / "project_input.schema.json"
    manifest_schema_path = schemas_dir / "manifest.schema.json"

    project_schema = ProjectInput.model_json_schema()
    manifest_schema = Manifest.model_json_schema()

    project_schema_path.write_text(
        json.dumps(project_schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    manifest_schema_path.write_text(
        json.dumps(manifest_schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


# Generate schemas on import to satisfy test expectations.
try:
    _generate_json_schemas()
except Exception:
    # Do not fail import if filesystem is not writable in some contexts.
    pass
