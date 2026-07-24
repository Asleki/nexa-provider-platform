"""
GitHub-ready tracker Markdown rendering primitives.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Mapping

from .architecture import ArchitectureRecord, ArchitectureSnapshot
from .files import detect_previous_milestone_impacts
from .models import TrackerRecord, TrackerRecordKind, TrackerStatus
from .progress import TrackerProgress


TRACKER_STATUS_ICON = {
    TrackerStatus.PLANNED: "🟦",
    TrackerStatus.IN_PROGRESS: "🟡",
    TrackerStatus.BLOCKED: "⛔",
    TrackerStatus.VALIDATED: "✅",
    TrackerStatus.COMPLETED: "✅",
    TrackerStatus.CANCELLED: "⚫",
}

ARCHITECTURE_STATUS_ICON = {
    "PLANNED": "🟦",
    "IN_PROGRESS": "🟡",
    "BLOCKED": "⛔",
    "VALIDATED": "✅",
    "COMPLETED": "✅",
    "RELEASED": "✅",
    "CANCELLED": "⚫",
}


def _architecture_record(
    record: TrackerRecord,
    architecture: ArchitectureSnapshot,
) -> ArchitectureRecord | None:
    if record.kind is not TrackerRecordKind.ARCHITECTURE:
        return None

    return architecture.require_record(
        record.architecture_record_id or ""
    )


def _title(
    record: TrackerRecord,
    architecture: ArchitectureSnapshot,
) -> str:
    canonical = _architecture_record(record, architecture)

    if canonical is not None:
        return canonical.title

    return record.title or "Untitled tracker record"


def _display_icon(
    record: TrackerRecord,
    architecture: ArchitectureSnapshot,
) -> str:
    canonical = _architecture_record(record, architecture)

    if canonical is not None:
        return ARCHITECTURE_STATUS_ICON.get(
            canonical.status,
            "🟦",
        )

    return TRACKER_STATUS_ICON[record.status]


def _canonical_status_label(
    record: TrackerRecord,
    architecture: ArchitectureSnapshot,
) -> str | None:
    canonical = _architecture_record(record, architecture)

    if canonical is None:
        return None

    return canonical.status.replace("_", " ").title()


def _tracker_status_label(record: TrackerRecord) -> str:
    return record.status.value.replace("_", " ").title()


def render_header(
    architecture: ArchitectureSnapshot,
    progress: TrackerProgress,
    *,
    generated_at: str,
    roadmap_sha256: str,
) -> list[str]:
    return [
        '<div align="center">',
        "",
        "# Nexa Provider Platform",
        "",
        "## Roadmap Engineering Tracker",
        "",
        f"**Architecture {architecture.version}** · "
        f"**{progress.architecture_completed}/{progress.architecture_total} "
        f"canonical records complete**",
        "",
        f"**Architectural progress:** "
        f"{progress.architecture_percentage:.2f}% · "
        f"**Tracked execution progress:** "
        f"{progress.tracker_percentage:.2f}%",
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


def render_summary(
    progress: TrackerProgress,
    records: Iterable[TrackerRecord],
) -> list[str]:
    records = tuple(records)
    commits = {commit.sha for record in records for commit in record.commits}
    files = {item.path for record in records for item in record.files}
    impacts = detect_previous_milestone_impacts(records)

    return [
        "## Engineering dashboard",
        "",
        "| Metric | Value |",
        "|---|---:|",
        f"| Canonical architecture records | "
        f"**{progress.architecture_total}** |",
        f"| Canonical architecture completed | "
        f"**{progress.architecture_completed}** |",
        f"| Architectural progress | "
        f"**{progress.architecture_percentage:.2f}%** |",
        f"| Tracker-owned records | "
        f"**{progress.tracker_total}** |",
        f"| Tracker records complete | "
        f"**{progress.tracker_completed}** |",
        f"| Engineering execution progress | "
        f"**{progress.tracker_percentage:.2f}%** |",
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

    ordered = sorted(
        records,
        key=lambda item: (
            numbers[item.tracker_id],
            item.tracker_id,
        ),
    )

    if not ordered:
        lines.extend(
            [
                "> No tracker-owned engineering records "
                "have been registered yet.",
                "",
            ]
        )
        return lines

    for record in ordered:
        number = numbers[record.tracker_id]
        icon = _display_icon(record, architecture)

        kind_label = {
            TrackerRecordKind.ARCHITECTURE:
                "Architecture-linked execution",
            TrackerRecordKind.EXTENSION:
                "Tracker-only extension",
            TrackerRecordKind.TRACKER_MILESTONE:
                "Tracker-only milestone",
        }[record.kind]

        canonical_status = _canonical_status_label(
            record,
            architecture,
        )
        tracker_status = _tracker_status_label(record)

        lines.extend(
            [
                f'<a id="{record.tracker_id}"></a>',
                f"### {icon} {number} — "
                f"{_title(record, architecture)}",
                "",
                f"> **Type:** {kind_label}",
                f"> **Tracker ID:** `{record.tracker_id}`",
            ]
        )

        if canonical_status is not None:
            lines.extend(
                [
                    f"> **Canonical status:** "
                    f"{canonical_status}",
                    f"> **Tracker execution status:** "
                    f"{tracker_status}",
                ]
            )
        else:
            lines.append(
                f"> **Status:** {tracker_status}"
            )

        lines.extend(
            [
                f"> **Created:** `{record.created_at}`",
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
                "<summary><strong>"
                "Open engineering history"
                "</strong></summary>",
                "",
            ]
        )

        if record.description:
            lines.extend(
                [
                    "#### Purpose",
                    "",
                    record.description,
                    "",
                ]
            )

        if record.commits:
            lines.extend(
                [
                    "#### Commits",
                    "",
                    "| Commit | Message | Timestamp | Author |",
                    "|---|---|---|---|",
                ]
            )

            for commit in record.commits:
                lines.append(
                    f"| `{commit.sha[:12]}` | "
                    f"{commit.message} | "
                    f"`{commit.committed_at}` | "
                    f"{commit.author or '—'} |"
                )

            lines.append("")

        if record.files:
            lines.extend(
                [
                    "#### Files",
                    "",
                    "| Action | Path | Original owner | Reason |",
                    "|---|---|---|---|",
                ]
            )

            for evidence in record.files:
                lines.append(
                    f"| {evidence.action} | "
                    f"`{evidence.path}` | "
                    f"`{evidence.owning_record_id or '—'}` | "
                    f"{evidence.reason or '—'} |"
                )

            lines.append("")

        if record.tests:
            lines.extend(["#### Tests", ""])
            lines.extend(
                f"- `{item}`"
                for item in record.tests
            )
            lines.append("")

        if record.notes:
            lines.extend(["#### Notes", ""])
            lines.extend(
                f"- {item}"
                for item in record.notes
            )
            lines.append("")

        lines.extend(
            [
                "</details>",
                "",
                "---",
                "",
            ]
        )

    return lines