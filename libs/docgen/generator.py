from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, select_autoescape

try:
    # Prefer python-markdown if available
    from markdown import markdown as md_to_html  # type: ignore
except Exception:  # pragma: no cover - optional dep
    md_to_html = None  # type: ignore


THEME_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
  body { background: #000000; color: #f3f4f6; font-family: Inter, 'JetBrains Mono', monospace; margin: 2em; text-indent: 2em; }
  h1 { color: #ff00ff; }
  h2, h3 { color: #39ff14; }
  code, pre { background: #0a0a0a; border: 1px solid #111; padding: .5em; border-radius: 6px; }
  a { color: #39ff14; }
  hr { border-color: #111; }
  .meta { color: #9ca3af; font-size: .9em; }
</style>
"""


def _env() -> Environment:
    templates_dir = Path(__file__).resolve().parent / "templates"
    env = Environment(
        loader=FileSystemLoader(str(templates_dir)),
        autoescape=select_autoescape(disabled_extensions=(".md",), default=True),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals["THEME_CSS"] = THEME_CSS
    return env


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def build_docs(project: Dict[str, Any]) -> Dict[str, str]:
    """
    Genera los documentos base del proyecto en Markdown y PDF.
    - Crea SRS.md, HLD.md, LLD.md a partir de plantillas Jinja2.
    - Convierte cada uno a PDF usando WeasyPrint si está disponible; si no, genera un HTML como fallback.
    - Guarda en artifacts/<project_id>/docs/ (en filesystem local). Devuelve rutas generadas.
    """
    proj_id = str(project.get("id") or project.get("run_id") or project.get("name") or "project")

    out_dir = Path("artifacts") / proj_id / "docs"
    _ensure_dir(out_dir)

    env = _env()
    context = {"project": project}

    outputs: Dict[str, str] = {}

    items = [
        ("SRS.md.j2", "SRS.md"),
        ("HLD.md.j2", "HLD.md"),
        ("LLD.md.j2", "LLD.md"),
    ]

    rendered_html_cache: Dict[str, str] = {}

    for tpl_name, md_name in items:
        template = env.get_template(tpl_name)
        md_content = template.render(**context)
        md_path = out_dir / md_name
        md_path.write_text(md_content, encoding="utf-8")
        outputs[md_name] = str(md_path)

        # Convert markdown to HTML (if markdown lib available) and wrap with theme CSS
        if md_to_html is not None:
            body_html = md_to_html(md_content)
        else:
            # Fallback: pre-wrap markdown as <pre> to at least keep formatting
            escaped = md_content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            body_html = f"<pre>{escaped}</pre>"

        # Render full HTML with CSS for PDF conversion
        html = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            f"{THEME_CSS}</head><body>{body_html}</body></html>"
        )
        rendered_html_cache[md_name] = html

    # Try to convert to PDF using WeasyPrint
    try:
        from weasyprint import HTML

        for md_name in ("SRS.md", "HLD.md", "LLD.md"):
            pdf_name = md_name.replace(".md", ".pdf")
            pdf_path = out_dir / pdf_name
            HTML(string=rendered_html_cache[md_name]).write_pdf(str(pdf_path))
            outputs[pdf_name] = str(pdf_path)
    except Exception:
        # Fallback: write HTML files instead of PDFs if WeasyPrint unavailable
        for md_name in ("SRS.md", "HLD.md", "LLD.md"):
            html_name = md_name.replace(".md", ".html")
            html_path = out_dir / html_name
            html_path.write_text(rendered_html_cache[md_name], encoding="utf-8")
            outputs[html_name] = str(html_path)

    return outputs
