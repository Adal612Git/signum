from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .models import Class, Relation


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def to_mermaid(classes: List[Class], relations: List[Relation]) -> str:
    """
    Exporta un diagrama de clases en formato Mermaid con tema oscuro y bordes azul neón (#00f0ff).
    """
    lines: List[str] = []
    # Mermaid init with dark theme and neon borders
    lines.append(
        "%%{init: { 'theme': 'dark', 'themeVariables': {\n"
        "  'primaryColor': '#000000',\n"
        "  'primaryBorderColor': '#00f0ff',\n"
        "  'lineColor': '#00f0ff',\n"
        "  'tertiaryBorderColor': '#00f0ff',\n"
        "  'fontFamily': 'Inter,JetBrains Mono,monospace'\n"
        "}} }%%"
    )
    lines.append("classDiagram")

    # Classes with attributes and methods
    for c in classes:
        lines.append(f"class {c.name}")
        if c.attributes or c.methods:
            lines.append(f"{c.name} : ")  # ensure class block exists
        for a in c.attributes:
            lines.append(f"{c.name} : {a}")
        for m in c.methods:
            lines.append(f"{c.name} : {m}()")

    # Relations mapping
    for r in relations:
        src, tgt = r.source, r.target
        t = r.type.lower()
        if t == "inheritance":
            # Mermaid: Base <|-- Derived  (Derived inherits Base)
            lines.append(f"{tgt} <|-- {src}")
        elif t == "association":
            lines.append(f"{src} --> {tgt}")
        elif t == "aggregation":
            lines.append(f"{src} o-- {tgt}")
        elif t == "composition":
            lines.append(f"{src} *-- {tgt}")
        elif t == "dependency":
            lines.append(f"{src} ..> {tgt}")
        elif t == "realization":
            lines.append(f"{tgt} <|.. {src}")
        else:
            # default to association if unknown
            lines.append(f"{src} --> {tgt}")

    return "\n".join(lines) + "\n"


def to_staruml_mdj(classes: List[Class], relations: List[Relation]) -> Dict[str, Any]:
    """Devuelve una estructura mínima compatible con StarUML (.mdj)."""

    # StarUML's .mdj is a JSON with elements typed by kind names (e.g., UMLClass, UMLModel)
    # Build a simple project -> model -> diagram elements structure.
    # IDs can be arbitrary strings; we'll use simple incremental IDs.
    def make_id(prefix: str, idx: int) -> str:
        return f"_{prefix}_{idx}"

    owned_elements: List[Dict[str, Any]] = []
    class_id_map: Dict[str, str] = {}

    # Create a top-level UMLModel containing classes
    model_id = make_id("model", 1)

    # Classes
    for i, c in enumerate(classes, start=1):
        cid = make_id("class", i)
        class_id_map[c.name] = cid
        owned_elements.append(
            {
                "_type": "UMLClass",
                "_id": cid,
                "name": c.name,
                "attributes": [
                    {
                        "_type": "UMLAttribute",
                        "_id": make_id("attr", i * 100 + j),
                        "name": attr,
                        "visibility": "public",
                    }
                    for j, attr in enumerate(c.attributes, start=1)
                ],
                "operations": [
                    {
                        "_type": "UMLOperation",
                        "_id": make_id("op", i * 100 + j),
                        "name": m,
                        "visibility": "public",
                    }
                    for j, m in enumerate(c.methods, start=1)
                ],
            }
        )

    # Relations
    for k, r in enumerate(relations, start=1):
        src_id = class_id_map.get(r.source)
        tgt_id = class_id_map.get(r.target)
        if not src_id or not tgt_id:
            continue
        rel_type = r.type.lower()
        type_map = {
            "association": "UMLAssociation",
            "aggregation": "UMLAssociation",
            "composition": "UMLAssociation",
            "inheritance": "UMLGeneralization",
            "realization": "UMLRealization",
            "dependency": "UMLDependency",
        }
        t = type_map.get(rel_type, "UMLAssociation")
        if t == "UMLGeneralization":
            # child -> parent
            owned_elements.append(
                {
                    "_type": "UMLGeneralization",
                    "_id": make_id("gen", k),
                    "source": {"$ref": src_id},
                    "target": {"$ref": tgt_id},
                }
            )
        elif t == "UMLAssociation":
            agg_kind = "none"
            if rel_type == "aggregation":
                agg_kind = "shared"
            elif rel_type == "composition":
                agg_kind = "composite"
            owned_elements.append(
                {
                    "_type": "UMLAssociation",
                    "_id": make_id("assoc", k),
                    "end1": {
                        "_type": "UMLAssociationEnd",
                        "_id": make_id("end", k * 10 + 1),
                        "reference": {"$ref": src_id},
                        "aggregation": "none",
                    },
                    "end2": {
                        "_type": "UMLAssociationEnd",
                        "_id": make_id("end", k * 10 + 2),
                        "reference": {"$ref": tgt_id},
                        "aggregation": agg_kind,
                    },
                }
            )
        else:
            owned_elements.append(
                {
                    "_type": t,
                    "_id": make_id("rel", k),
                    "source": {"$ref": src_id},
                    "target": {"$ref": tgt_id},
                }
            )

    project: Dict[str, Any] = {
        "_type": "Project",
        "_id": make_id("proj", 1),
        "name": "Signum UML",
        "ownedElements": [
            {
                "_type": "UMLModel",
                "_id": model_id,
                "name": "Model",
                "ownedElements": owned_elements,
            }
        ],
    }
    return project


def build_uml(project: Dict) -> Dict[str, str]:
    """
    Usa datos del proyecto para poblar clases/relaciones de ejemplo y genera:
      - artifacts/<project_id>/uml/diagrams.md (Mermaid)
      - artifacts/<project_id>/uml/signum.mdj (StarUML JSON)

    Devuelve un dict con rutas generadas.
    """
    proj_id = str(project.get("id") or project.get("run_id") or project.get("name") or "project")
    out_dir = Path("artifacts") / proj_id / "uml"
    _ensure_dir(out_dir)

    # Poblar clases/relaciones simples a partir de los datos del proyecto (ejemplo)
    # NOTA: Antes se obtenían `pname` y `owner` desde `project`, pero no se usaban.
    # Se eliminaron para evitar la advertencia de variables sin usar, que ruff
    # marcaba como error y bloqueaba el commit.

    classes = [
        Class(
            name="Project",
            attributes=["name: str", "description: str", "owner: str"],
            methods=["build", "deploy"],
        ),
        Class(name="Owner", attributes=["name: str"], methods=["notify"]),
        Class(name="Artifact", attributes=["id: str", "type: str"], methods=["serialize"]),
    ]
    relations = [
        Relation(source="Project", target="Owner", type="association"),
        Relation(source="Artifact", target="Project", type="dependency"),
    ]

    # Mermaid
    mermaid_str = to_mermaid(classes, relations)
    mermaid_path = out_dir / "diagrams.md"
    mermaid_path.write_text(mermaid_str, encoding="utf-8")

    # StarUML (.mdj)
    mdj_dict = to_staruml_mdj(classes, relations)
    mdj_path = out_dir / "signum.mdj"
    mdj_path.write_text(json.dumps(mdj_dict, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "diagrams.md": str(mermaid_path),
        "signum.mdj": str(mdj_path),
        "base_dir": str(out_dir),
    }
