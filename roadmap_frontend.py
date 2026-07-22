#!/usr/bin/env python3
"""
Generate the GitHub-ready Nexa Provider Platform ROADMAP.md frontend.

The canonical source remains roadmap_data.py. This generator converts all
canonical roadmap records into a polished Markdown dashboard with live counts,
progress indicators, navigation, root-phase summaries, and collapsible detail
sections.

Usage:
    python roadmap_frontend.py
    python roadmap_frontend.py --output ROADMAP.md
    python roadmap_frontend.py --check
"""

from __future__ import annotations

import argparse
import hashlib
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence

import roadmap_data
from roadmap.models import Milestone, RoadmapMetadata, RoadmapSnapshot, milestones_from_mappings
from roadmap.progress import summarize_progress
from roadmap.queries import build_number_index, get_roots, sort_by_sequence
from roadmap.statuses import RoadmapStatus


DEFAULT_OUTPUT = Path("ROADMAP.md")
BAR_WIDTH = 30


class RoadmapFrontendError(RuntimeError):
    """Base error for roadmap frontend generation."""


@dataclass(frozen=True, slots=True)
class FrontendStats:
    total: int
    completed: int
    planned: int
    roots: int
    percentage: float


def build_snapshot() -> RoadmapSnapshot:
    """Build the canonical immutable roadmap snapshot."""

    metadata = RoadmapMetadata(
        title=roadmap_data.ROADMAP_TITLE,
        version=roadmap_data.ROADMAP_VERSION,
        start=roadmap_data.ROADMAP_START,
        end=roadmap_data.ROADMAP_END,
        allowed_statuses=tuple(roadmap_data.ALLOWED_STATUSES),
        boundaries=getattr(roadmap_data, "ROADMAP_BOUNDARIES", {}),
    )
    milestones = milestones_from_mappings(roadmap_data.MILESTONES)
    return RoadmapSnapshot(metadata=metadata, milestones=milestones)


def calculate_stats(snapshot: RoadmapSnapshot) -> FrontendStats:
    """Calculate the headline dashboard statistics."""

    summary = summarize_progress(snapshot)
    return FrontendStats(
        total=summary.total,
        completed=summary.complete,
        planned=summary.incomplete,
        roots=len(get_roots(snapshot)),
        percentage=float(summary.percentage),
    )


def progress_bar(completed: int, total: int, width: int = BAR_WIDTH) -> str:
    """Return a deterministic Unicode progress bar."""

    if total < 0 or completed < 0 or completed > total:
        raise RoadmapFrontendError("invalid progress values")
    if width < 1:
        raise RoadmapFrontendError("progress bar width must be positive")
    filled = 0 if total == 0 else round((completed / total) * width)
    return "█" * filled + "░" * (width - filled)


def status_icon(status: RoadmapStatus) -> str:
    """Return the presentation icon for a roadmap status."""

    if status is RoadmapStatus.COMPLETED:
        return "✅"
    if status is RoadmapStatus.PLANNED:
        return "🟦"
    if status is RoadmapStatus.IN_PROGRESS:
        return "🟡"
    if status is RoadmapStatus.BLOCKED:
        return "🔴"
    if status is RoadmapStatus.CANCELLED:
        return "⚫"
    return "⚪"


def status_label(status: RoadmapStatus) -> str:
    return status.value.replace("_", " ").title()


def anchor_for(number: str) -> str:
    return number.lower().replace(".", "")


def descendants_of(
    root: Milestone,
    records: Sequence[Milestone],
) -> tuple[Milestone, ...]:
    """Return all descendants of one root using canonical semantic numbering."""

    prefix = root.number + "."
    return tuple(
        item
        for item in records
        if item.number == root.number or item.number.startswith(prefix)
    )


def render_header(snapshot: RoadmapSnapshot, stats: FrontendStats) -> list[str]:
    bar = progress_bar(stats.completed, stats.total)
    return [
        "<div align=\"center\">",
        "",
        "# Nexa Provider Platform",
        "",
        "## Engineering Roadmap Frontend",
        "",
        f"**Version {snapshot.metadata.version}** · "
        f"**{snapshot.metadata.start} → {snapshot.metadata.end}** · "
        f"**{stats.total} canonical records**",
        "",
        f"`{bar}` **{stats.percentage:.2f}%**",
        "",
        f"**{stats.completed} completed** · "
        f"**{stats.planned} planned** · "
        f"**{stats.roots} root milestones**",
        "",
        "</div>",
        "",
        "> [!IMPORTANT]",
        "> This document is generated from `roadmap_data.py`. "
        "Do not edit milestone content here by hand. "
        "Run `python roadmap_frontend.py` after changing the canonical dataset.",
        "",
        "---",
        "",
    ]


def render_dashboard(stats: FrontendStats) -> list[str]:
    return [
        "## Dashboard",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Overall progress | **{stats.percentage:.2f}%** |",
        f"| Completed milestones | **{stats.completed}** |",
        f"| Planned milestones | **{stats.planned}** |",
        f"| Total roadmap records | **{stats.total}** |",
        f"| Root milestones | **{stats.roots}** |",
        "",
        "### Status key",
        "",
        "- ✅ **Completed** — implemented roadmap work.",
        "- 🟦 **Planned** — approved work that has not yet been completed.",
        "- 🟡 **In progress** — active work, when introduced into canonical data.",
        "- 🔴 **Blocked** — work waiting on a prerequisite or decision.",
        "",
        "---",
        "",
    ]


def render_navigation(
    roots: Sequence[Milestone],
    records: Sequence[Milestone],
) -> list[str]:
    lines = [
        "## Roadmap navigation",
        "",
        "Jump directly to a root milestone:",
        "",
    ]
    for root in roots:
        branch = descendants_of(root, records)
        complete = sum(item.status is RoadmapStatus.COMPLETED for item in branch)
        percentage = (complete / len(branch) * 100) if branch else 0.0
        lines.append(
            f"- [{status_icon(root.status)} **{root.number} — {root.title}**]"
            f"(#{anchor_for(root.number)}) "
            f"— {complete}/{len(branch)} complete ({percentage:.1f}%)"
        )
    lines.extend(["", "---", ""])
    return lines


def render_root_summary(
    roots: Sequence[Milestone],
    records: Sequence[Milestone],
) -> list[str]:
    lines = [
        "## Root milestone overview",
        "",
        "| Root | Title | Status | Records | Complete | Progress |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for root in roots:
        branch = descendants_of(root, records)
        complete = sum(item.status is RoadmapStatus.COMPLETED for item in branch)
        percentage = (complete / len(branch) * 100) if branch else 0.0
        lines.append(
            f"| [{root.number}](#{anchor_for(root.number)}) "
            f"| {root.title} "
            f"| {status_icon(root.status)} {status_label(root.status)} "
            f"| {len(branch)} "
            f"| {complete} "
            f"| {percentage:.1f}% |"
        )
    lines.extend(["", "---", ""])
    return lines


def render_milestone(item: Milestone) -> list[str]:
    indent = "&nbsp;" * (item.depth * 4)
    dependency_text = (
        ", ".join(f"`{number}`" for number in item.dependencies)
        if item.dependencies
        else "None"
    )
    lines = [
        f"{indent}{status_icon(item.status)} "
        f"**`{item.number}` — {item.title}**",
        "",
        f"{indent}- **Status:** {status_label(item.status)}",
        f"{indent}- **Priority:** {item.priority}",
        f"{indent}- **Dependencies:** {dependency_text}",
        f"{indent}- **Record ID:** `{item.record_id}`",
        f"{indent}- **Semantic path:** `{item.semantic_path}`",
    ]

    if item.commit_hash:
        lines.append(f"{indent}- **Commit:** `{item.commit_hash}`")
    if item.verification_state:
        lines.append(
            f"{indent}- **Verification:** {item.verification_state}"
        )
    if item.notes:
        lines.append(
            f"{indent}- **Notes:** {'; '.join(item.notes)}"
        )
    if item.test_information:
        lines.append(
            f"{indent}- **Tests:** {'; '.join(item.test_information)}"
        )
    if item.passing_tests is not None:
        lines.append(
            f"{indent}- **Passing tests:** {item.passing_tests}"
        )

    lines.append("")
    return lines


def render_roots(
    roots: Sequence[Milestone],
    records: Sequence[Milestone],
) -> list[str]:
    lines = ["## Complete roadmap", ""]

    for root in roots:
        branch = descendants_of(root, records)
        complete = sum(item.status is RoadmapStatus.COMPLETED for item in branch)
        percentage = (complete / len(branch) * 100) if branch else 0.0
        bar = progress_bar(complete, len(branch), width=20)

        lines.extend([
            f'<a id="{anchor_for(root.number)}"></a>',
            f"### {status_icon(root.status)} {root.number} — {root.title}",
            "",
            f"`{bar}` **{complete}/{len(branch)} complete ({percentage:.1f}%)**",
            "",
            "<details>",
            f"<summary><strong>Open {root.number} roadmap records "
            f"({len(branch)} items)</strong></summary>",
            "",
        ])

        for item in branch:
            lines.extend(render_milestone(item))

        lines.extend([
            "</details>",
            "",
            "[⬆ Back to roadmap navigation](#roadmap-navigation)",
            "",
            "---",
            "",
        ])

    return lines


def render_footer(snapshot: RoadmapSnapshot, stats: FrontendStats) -> list[str]:
    dataset_hash = hashlib.sha256(
        repr(tuple(item.to_mapping() for item in snapshot.milestones)).encode("utf-8")
    ).hexdigest()
    return [
        "## Generation information",
        "",
        "| Property | Value |",
        "|---|---|",
        f"| Canonical source | `roadmap_data.py` |",
        f"| Generator | `roadmap_frontend.py` |",
        f"| Roadmap version | `{snapshot.metadata.version}` |",
        f"| Records rendered | `{stats.total}` |",
        f"| Canonical content checksum | `{dataset_hash}` |",
        "",
        "> The generated timestamp is intentionally omitted so identical "
        "canonical data produces identical `ROADMAP.md` output.",
        "",
    ]


def render_roadmap(snapshot: RoadmapSnapshot) -> str:
    """Render the entire GitHub-ready roadmap frontend."""

    records = sort_by_sequence(snapshot)
    roots = get_roots(records)
    stats = calculate_stats(snapshot)

    lines: list[str] = []
    lines.extend(render_header(snapshot, stats))
    lines.extend(render_dashboard(stats))
    lines.extend(render_navigation(roots, records))
    lines.extend(render_root_summary(roots, records))
    lines.extend(render_roots(roots, records))
    lines.extend(render_footer(snapshot, stats))

    return "\n".join(lines).rstrip() + "\n"


def write_roadmap(
    output: Path = DEFAULT_OUTPUT,
    *,
    check: bool = False,
) -> str:
    """Generate ROADMAP.md, or check whether an existing file is current."""

    snapshot = build_snapshot()
    rendered = render_roadmap(snapshot)
    output = Path(output)

    if check:
        if not output.exists():
            raise RoadmapFrontendError(f"{output} does not exist")
        current = output.read_text(encoding="utf-8")
        if current != rendered:
            raise RoadmapFrontendError(
                f"{output} is out of date; run roadmap_frontend.py"
            )
        return rendered

    output.write_text(rendered, encoding="utf-8", newline="\n")
    return rendered


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate the Nexa Provider Platform ROADMAP.md frontend."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="output Markdown path (default: ROADMAP.md)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the existing output is missing or out of date",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        rendered = write_roadmap(args.output, check=args.check)
    except RoadmapFrontendError as error:
        print(f"ERROR: {error}")
        return 1

    digest = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    action = "Verified" if args.check else "Generated"
    print(f"{action} {args.output}")
    print(f"Records: {len(build_snapshot().milestones)}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
