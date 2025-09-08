from __future__ import annotations

import json
import zlib
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ------------------------
# Models and scheduling
# ------------------------


@dataclass
class Task:
    id: str
    name: str
    duration_days: int
    deps: List[str]
    start: Optional[date] = None
    # Computed
    start_date: Optional[date] = None
    end_date: Optional[date] = None


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _parse_date(s: Optional[str]) -> Optional[date]:
    if not s:
        return None
    # Accept YYYY-MM-DD or ISO
    try:
        return datetime.fromisoformat(s).date()
    except Exception:
        # Fallback: strict date
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return None


def _format_date(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def _toposort(tasks: Dict[str, Task]) -> List[str]:
    indeg: Dict[str, int] = {tid: 0 for tid in tasks}
    graph: Dict[str, List[str]] = {tid: [] for tid in tasks}
    for t in tasks.values():
        for dep in t.deps:
            if dep not in tasks:
                # Ignore missing dep references silently; they just won't constrain scheduling
                continue
            indeg[t.id] += 1
            graph[dep].append(t.id)

    queue: List[str] = [tid for tid, d in indeg.items() if d == 0]
    order: List[str] = []
    i = 0
    while i < len(queue):
        u = queue[i]
        i += 1
        order.append(u)
        for v in graph.get(u, []):
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)

    if len(order) != len(tasks):
        raise ValueError("Cycle detected in task dependencies")
    return order


def schedule_backlog(backlog: List[Dict[str, Any]], base_date: Optional[date] = None) -> List[Task]:
    # Build Task objects
    tasks: Dict[str, Task] = {}
    for item in backlog:
        tid = str(item.get("id"))
        name = str(item.get("name") or tid)
        duration = int(item.get("duration", 1))
        deps = [str(d) for d in (item.get("dependencies") or [])]
        start = _parse_date(item.get("start"))
        tasks[tid] = Task(id=tid, name=name, duration_days=max(1, duration), deps=deps, start=start)

    # Determine base date: explicit min provided start or today()
    provided_starts = [t.start for t in tasks.values() if t.start is not None]
    base = base_date or (min(provided_starts) if provided_starts else date.today())

    order = _toposort(tasks)

    # Compute start/end dates
    for tid in order:
        t = tasks[tid]
        # Earliest allowed start considering deps
        dep_end = base
        for dep_id in t.deps:
            dep = tasks.get(dep_id)
            if not dep or not dep.end_date:
                continue
            if dep.end_date > dep_end:
                dep_end = dep.end_date
        desired_start = t.start or base
        start_date = desired_start if desired_start >= dep_end else dep_end
        end_date = start_date + timedelta(days=t.duration_days)
        t.start_date = start_date
        t.end_date = end_date

    return [tasks[tid] for tid in order]


# ------------------------
# Exports
# ------------------------


def to_mermaid_gantt(tasks: List[Task], title: str = "Project Plan") -> str:
    lines: List[str] = []
    # Dark theme + custom colors
    lines.append(
        "%%{init: { 'theme': 'dark', 'themeVariables': {\n"
        "  'background': '#000000',\n"
        "  'lineColor': '#00ff7f',\n"
        "  'taskBkgColor': '#d600ff',\n"
        "  'taskBorderColor': '#d600ff',\n"
        "  'fontFamily': 'Inter,JetBrains Mono,monospace'\n"
        "}} }%%"
    )
    lines.append("gantt")
    lines.append("dateFormat YYYY-MM-DD")
    lines.append(f"title {title}")

    # Group all tasks in a single section named 'Backlog'
    lines.append("section Backlog")
    for t in tasks:
        start = _format_date(t.start_date or date.today())
        dur = f"{t.duration_days}d"
        # Use explicit start + duration for portability across renderers
        # Mermaid task syntax: <desc> :<id>, <start>, <duration>
        safe_name = t.name.replace("\n", " ")
        lines.append(f"{safe_name} :{t.id}, {start}, {dur}")
    return "\n".join(lines) + "\n"


def export_json(tasks: List[Task]) -> Dict[str, Any]:
    return {
        "tasks": [
            {
                "id": t.id,
                "name": t.name,
                "duration": t.duration_days,
                "dependencies": list(t.deps),
                "start": _format_date(t.start_date or date.today()),
                "end": _format_date(t.end_date or (t.start_date or date.today())),
            }
            for t in tasks
        ]
    }


# ------------------------
# Minimal PNG renderer (fallback when CLI not available)
# ------------------------


def _save_png_basic_gantt(tasks: List[Task], path: Path) -> None:
    """Render a minimal PNG preview with dark background, green grid lines and purple bars.

    This is a lightweight fallback that does not require external tools.
    It is not a full Mermaid renderer, but satisfies the artifact requirements.
    """

    # Layout
    padding_x = 20
    padding_y = 20
    row_h = 24
    gap = 10
    header_h = 30
    n = len(tasks)
    height = padding_y * 2 + header_h + n * (row_h + gap)

    # Compute timeline span in days
    start_min = min((t.start_date or date.today()) for t in tasks)
    end_max = max((t.end_date or (t.start_date or date.today())) for t in tasks)
    span_days = max(1, (end_max - start_min).days)
    width = max(600, padding_x * 2 + span_days * 20)  # 20px per day

    # Colors RGBA
    black = (0, 0, 0, 255)
    green = (0, 255, 127, 255)  # #00ff7f
    purple = (214, 0, 255, 255)  # #d600ff
    # white = (240, 240, 240, 255)

    # Pixel buffer (RGBA)
    buf = bytearray(width * height * 4)

    def set_px(x: int, y: int, c: Tuple[int, int, int, int]) -> None:
        if not (0 <= x < width and 0 <= y < height):
            return
        i = (y * width + x) * 4
        buf[i : i + 4] = bytes(c)

    # Fill background
    for y in range(height):
        for x in range(width):
            set_px(x, y, black)

    # Draw header baseline
    for x in range(padding_x, width - padding_x):
        set_px(x, padding_y + header_h, green)

    # Draw vertical grid every ~5 days
    px_per_day = (width - 2 * padding_x) / span_days
    for d in range(0, span_days + 1, 5):
        x = int(padding_x + d * px_per_day)
        for y in range(padding_y + header_h, height - padding_y):
            set_px(x, y, (0, 80, 40, 255))

    # Draw task bars
    for idx, t in enumerate(tasks):
        y_top = padding_y + header_h + idx * (row_h + gap) + 4
        y_bottom = y_top + row_h - 8
        sd = t.start_date or start_min
        ed = t.end_date or sd
        s_off = (sd - start_min).days
        e_off = (ed - start_min).days
        x1 = int(padding_x + s_off * px_per_day)
        x2 = int(padding_x + e_off * px_per_day)
        if x2 <= x1:
            x2 = x1 + max(2, int(px_per_day))
        for y in range(y_top, y_bottom):
            for x in range(x1, min(x2, width - padding_x)):
                set_px(x, y, purple)
        # Left/right border in green
        for y in range(y_top, y_bottom):
            set_px(x1, y, green)
            set_px(min(x2, width - padding_x) - 1, y, green)

    # Encode PNG
    def _chunk(tag: bytes, data: bytes) -> bytes:
        from struct import pack

        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return pack(">I", len(data)) + tag + data + pack(">I", crc)

    from struct import pack

    ihdr = pack(
        ">IIBBBBB",
        width,
        height,
        8,  # bit depth
        6,  # color type RGBA
        0,  # compression
        0,  # filter
        0,  # interlace
    )

    # Add scanline filter byte 0 per line
    scanlines = bytearray()
    stride = width * 4
    for y in range(height):
        scanlines.append(0)
        scanlines.extend(buf[y * stride : (y + 1) * stride])
    idat = zlib.compress(bytes(scanlines), level=6)

    png = bytearray()
    png.extend(b"\x89PNG\r\n\x1a\n")
    png.extend(_chunk(b"IHDR", ihdr))
    png.extend(_chunk(b"IDAT", idat))
    png.extend(_chunk(b"IEND", b""))

    path.write_bytes(png)


# ------------------------
# Public API
# ------------------------


def build_gantt(project: Dict[str, Any]) -> Dict[str, str]:
    """
    Genera plan Gantt a partir de un backlog simple y exporta:
      - artifacts/<project_id>/plan/gantt.json
      - artifacts/<project_id>/plan/gantt.mmd
      - artifacts/<project_id>/plan/gantt.png

    El backlog se toma de `project.get("backlog")` como lista de dicts:
      { id, name, duration (días), dependencies, start (YYYY-MM-DD opcional) }
    """
    proj_id = str(project.get("id") or project.get("run_id") or project.get("name") or "project")
    out_dir = Path("artifacts") / proj_id / "plan"
    _ensure_dir(out_dir)

    backlog = project.get("backlog") or []
    if not isinstance(backlog, list):
        raise ValueError("project.backlog must be a list")

    tasks = schedule_backlog(backlog)

    # Export JSON
    data = export_json(tasks)
    json_path = out_dir / "gantt.json"
    json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Export Mermaid
    title = str(project.get("name") or proj_id)
    mmd_str = to_mermaid_gantt(tasks, title=title)
    mmd_path = out_dir / "gantt.mmd"
    mmd_path.write_text(mmd_str, encoding="utf-8")

    # Render PNG (try external tools if present; otherwise fallback renderer)
    png_path = out_dir / "gantt.png"
    _render_png(mmd_path, png_path, tasks)

    return {
        "gantt.json": str(json_path),
        "gantt.mmd": str(mmd_path),
        "gantt.png": str(png_path),
        "base_dir": str(out_dir),
    }


def _render_png(mmd_path: Path, png_path: Path, tasks: List[Task]) -> None:
    # Try mermaid-cli if available
    try:
        import shutil

        mmdc = shutil.which("mmdc")
        if mmdc:
            import subprocess

            subprocess.run([mmdc, "-i", str(mmd_path), "-o", str(png_path)], check=True)
            if png_path.exists() and png_path.stat().st_size > 0:
                return
    except Exception:
        pass

    # Try py-mermaid if installed
    try:
        from mermaid import Mermaid

        diagram = Mermaid(str(mmd_path.read_text(encoding="utf-8")))
        png_bytes = diagram.to_png()
        png_path.write_bytes(png_bytes)
        if png_path.exists() and png_path.stat().st_size > 0:
            return
    except Exception:
        pass

    # Fallback basic PNG renderer
    _save_png_basic_gantt(tasks, png_path)
