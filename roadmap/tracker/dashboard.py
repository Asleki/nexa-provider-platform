"""
GitHub-ready tracker Markdown rendering primitives.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Mapping

from .architecture import ArchitectureSnapshot
from .files import detect_previous_milestone_impacts
from .models import TrackerRecord, TrackerRecordKind, TrackerStatus
from .progress import TrackerProgress


STATUS_ICON = {
    TrackerStatus.PLANNED: "🟦",
    TrackerStatus.IN_PROGRESS: "🟡",
    TrackerStatus.BLOCKED: "⛔",
    TrackerStatus.VALIDATED: "✅",
    TrackerStatus.COMPLETED: "✅",
    TrackerStatus.CANCELLED: "⚫",
}


def _title(
    record: TrackerRecord,
    architecture: ArchitectureSnapshot,
) -> str:
    if record.kind is TrackerRecordKind.ARCHITECTURE:
        return architecture.require_record(record.architecture_record_id or "").title
    return record.title or "Untitled tracker record"


def render_header(
    architecture: ArchitectureSnapshot,
    progress: TrackerProgress,
    *,
    generated_at: str,
    roadmap_sha256: str,
) -> list[str]:
    return [
        "<div align=\"center\">",
        "",
        "# Nexa Provider Platform",
        "",
        "## Roadmap Engineering Tracker",
        "",
        f"**Architecture {architecture.version}** · "
        f"**{progress.architecture_completed}/{progress.architecture_total} "
        f"canonical records complete**",
        "",
        f"**Architectural progress:** {progress.architecture_percentage:.2f}% · "
        f"**Tracked execution progress:** {progress.tracker_percentage:.2f}%",
        "",
        "</div>",
        "",
        "> [!IMPORTANT]",
        "> `ROADMAP.md` is the architectural authority. This tracker records "
        "engineering execution, extensions, files, tests, commits and timestamps. "
        "Tracker-only records never alter the canonical roadmap.",
        "",
        "<!-- tracker-sync",
        f"architecture_snapshot_sha256: {architecture.sha256}",
        f"roadmap_md_sha256: {roadmap_sha256}",
        f"generated_at: {generated_at}",
        "-->",
        "",
        "---",
        "",
    ]


def render_summary(progress: TrackerProgress, records: Iterable[TrackerRecord]) -> list[str]:
    records = tuple(records)
    commits = {c.sha for r in records for c in r.commits}
    files = {f.path for r in records for f in r.files}
    impacts = detect_previous_milestone_impacts(records)
    return [
        "## Engineering dashboard",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Canonical architecture records | **{progress.architecture_total}** |",
        f"| Canonical architecture completed | **{progress.architecture_completed}** |",
        f"| Architectural progress | **{progress.architecture_percentage:.2f}%** |",
        f"| Tracker-owned records | **{progress.tracker_total}** |",
        f"| Tracker records complete | **{progress.tracker_completed}** |",
        f"| Engineering execution progress | **{progress.tracker_percentage:.2f}%** |",
        f"| Unique commits recorded | **{len(commits)}** |",
        f"| Unique files recorded | **{len(files)}** |",
        f"| Previous-milestone impacts | **{len(impacts)}** |",
        "",
        "---",
        "",
    ]


def render_record_cards(
    architecture: ArchitectureSnapshot,
    records: Iterable[TrackerRecord],
    numbers: Mapping[str, str],
) -> list[str]:
    lines = ["## Milestone cards", ""]
    ordered = sorted(records, key=lambda item: (numbers[item.tracker_id], item.tracker_id))
    if not ordered:
        lines.extend([
            "> No tracker-owned engineering records have been registered yet.",
            "",
        ])
        return lines

    for record in ordered:
        number = numbers[record.tracker_id]
        icon = STATUS_ICON[record.status]
        kind_label = {
            TrackerRecordKind.ARCHITECTURE: "Architecture-linked execution",
            TrackerRecordKind.EXTENSION: "Tracker-only extension",
            TrackerRecordKind.TRACKER_MILESTONE: "Tracker-only milestone",
        }[record.kind]
        lines.extend([
            f'<a id="{record.tracker_id}"></a>',
            f"### {icon} {number} — {_title(record, architecture)}",
            "",
            f"> **Type:** {kind_label}  ",
            f"> **Tracker ID:** `{record.tracker_id}`  ",
            f"> **Status:** {record.status.value.replace('_', ' ').title()}  ",
            f"> **Created:** `{record.created_at}`  ",
            f"> **Updated:** `{record.updated_at}`",
            "",
            "| Evidence | Count |",
            "|---|---:|",
            f"| Commits | **{len(record.commits)}** |",
            f"| Files | **{len(record.files)}** |",
            f"| Tests | **{len(record.tests)}** |",
            f"| Notes | **{len(record.notes)}** |",
            "",
            "<details>",
            "<summary><strong>Open engineering history</strong></summary>",
            "",
        ])
        if record.description:
            lines.extend(["#### Purpose", "", record.description, ""])
        if record.commits:
            lines.extend([
                "#### Commits", "",
                "| Commit | Message | Timestamp | Author |",
                "|---|---|---|---|",
            ])
            for commit in record.commits:
                lines.append(
                    f"| `{commit.sha[:12]}` | {commit.message} | "
                    f"`{commit.committed_at}` | {commit.author or '—'} |"
                )
            lines.append("")
        if record.files:
            lines.extend([
                "#### Files", "",
                "| Action | Path | Original owner | Reason |",
                "|---|---|---|---|",
            ])
            for evidence in record.files:
                lines.append(
                    f"| {evidence.action} | `{evidence.path}` | "
                    f"`{evidence.owning_record_id or '—'}` | "
                    f"{evidence.reason or '—'} |"
                )
            lines.append("")
        if record.tests:
            lines.extend(["#### Tests", ""])
            lines.extend(f"- `{item}`" for item in record.tests)
            lines.append("")
        if record.notes:
            lines.extend(["#### Notes", ""])
            lines.extend(f"- {item}" for item in record.notes)
            lines.append("")
        lines.extend(["</details>", "", "---", ""])
    return lines
