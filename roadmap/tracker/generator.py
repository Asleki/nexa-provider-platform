"""
Deterministic ROADMAP_TRACKER.md generator.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .architecture import ArchitectureSnapshot
from .dashboard import render_header, render_record_cards, render_summary
from .extensions import resolve_display_numbers
from .models import TrackerRecord
from .progress import calculate_progress
from .validation import file_sha256


DEFAULT_OUTPUT = Path("ROADMAP_TRACKER.md")


def render_tracker(
    architecture: ArchitectureSnapshot,
    records: Iterable[TrackerRecord],
    *,
    generated_at: str,
    roadmap_path: Path,
) -> str:
    records = tuple(records)
    progress = calculate_progress(architecture, records)
    numbers = resolve_display_numbers(architecture, records)
    lines: list[str] = []
    lines.extend(
        render_header(
            architecture,
            progress,
            generated_at=generated_at,
            roadmap_sha256=file_sha256(roadmap_path),
        )
    )
    lines.extend(render_summary(progress, records))
    lines.extend(render_record_cards(architecture, records, numbers))
    return "\n".join(lines).rstrip() + "\n"


def write_tracker(
    architecture: ArchitectureSnapshot,
    records: Iterable[TrackerRecord],
    *,
    generated_at: str,
    roadmap_path: Path = Path("ROADMAP.md"),
    output: Path = DEFAULT_OUTPUT,
) -> str:
    rendered = render_tracker(
        architecture,
        records,
        generated_at=generated_at,
        roadmap_path=roadmap_path,
    )
    output = Path(output)
    if output.name in {"ROADMAP.md", "roadmap_data.py", "roadmap_frontend.py"}:
        raise ValueError("tracker output cannot overwrite architecture files")
    output.write_text(rendered, encoding="utf-8", newline="\n")
    return rendered
