from __future__ import annotations

from typing import Any, Dict

try:
    from fpdf import FPDF  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    FPDF = None  # type: ignore

from ._utils import artifacts_base, ensure_dir, load_artifacts, write_export_result


def export_to_pdf(project_id: str) -> Dict[str, Any]:
    if FPDF is None:
        return {"status": "failed", "error": "Missing fpdf2 package"}

    try:
        artifacts = load_artifacts(project_id)
        docs = artifacts.get("docs") or {}
        intro = str(docs.get("intro") or "").strip()
        usage = str(docs.get("usage") or "").strip()
        if not intro and not usage:
            result = {"status": "failed", "error": "docs.json is missing or empty"}
            write_export_result(project_id, "pdf", result)
            return result

        base = artifacts_base(project_id) / "exports"
        ensure_dir(base)
        path = base / "docs.pdf"

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()

        # Neon style headers
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(255, 0, 255)  # Magenta neon
        pdf.cell(0, 10, "SIGNUM Documentation", ln=1)

        pdf.set_font("Helvetica", "", 12)
        pdf.set_text_color(0, 0, 0)  # Body text in black
        if intro:
            pdf.set_text_color(57, 255, 20)  # Neon green
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Intro", ln=1)
            pdf.set_font("Helvetica", "", 12)
            pdf.set_text_color(0, 0, 0)
            for line in intro.splitlines():
                pdf.multi_cell(0, 8, line)

        if usage:
            pdf.ln(4)
            pdf.set_text_color(57, 255, 20)
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 10, "Usage", ln=1)
            pdf.set_font("Helvetica", "", 12)
            pdf.set_text_color(0, 0, 0)
            for line in usage.splitlines():
                pdf.multi_cell(0, 8, line)

        pdf.output(str(path))
        result = {"status": "ok", "path": str(path)}
        write_export_result(project_id, "pdf", result)
        return result
    except Exception as e:  # noqa: BLE001
        result = {"status": "failed", "error": str(e)}
        write_export_result(project_id, "pdf", result)
        return result
