from __future__ import annotations

import json
from typing import Any, Dict

import typer

from .github import export_to_github
from .trello import export_to_trello
from .nexus_ops import export_to_nexus_ops
from .pdf import export_to_pdf


app = typer.Typer(help="Signum Export Manager CLI")


def _print_result(result: Dict[str, Any]) -> None:
    typer.echo(json.dumps(result, indent=2, ensure_ascii=False))


@app.command()
def trello(project_id: str) -> None:
    """Export backlog to Trello."""
    res = export_to_trello(project_id)
    _print_result(res)


@app.command()
def github(project_id: str) -> None:
    """Export docs/backlog to GitHub (repo + issues)."""
    res = export_to_github(project_id)
    _print_result(res)


@app.command()
def nexus_ops(project_id: str) -> None:
    """Consolidate artifacts into a Nexus Ops payload (local file)."""
    res = export_to_nexus_ops(project_id)
    _print_result(res)


@app.command()
def pdf(project_id: str) -> None:
    """Render docs.json to a neon-styled PDF."""
    res = export_to_pdf(project_id)
    _print_result(res)


def main() -> None:
    app()


if __name__ == "__main__":
    main()
