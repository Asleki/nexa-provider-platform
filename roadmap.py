#!/usr/bin/env python3
"""
Nexa Provider Platform (NPP)
File: roadmap.py

Interactive command-line dashboard for the NPP engineering roadmap.

This file reads roadmap_data.py as the authoritative source of truth. It does
not duplicate milestone data and does not directly modify roadmap records.

Usage examples
--------------
python roadmap.py
python roadmap.py progress
python roadmap.py current
python roadmap.py next
python roadmap.py status
python roadmap.py show M012.6
python roadmap.py tree M012.6
python roadmap.py completed --roots
python roadmap.py planned --roots
python roadmap.py verify
python roadmap.py json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

try:
    import roadmap_data as data
except ImportError as exc:
    raise SystemExit(
        "❌ Unable to import roadmap_data.py.\n"
        "Save roadmap.py and roadmap_data.py in the same project directory."
    ) from exc


EXIT_OK = 0
EXIT_INVALID = 2
BAR_WIDTH = 30

STATUS_ICONS = {
    "COMPLETED": "✅",
    "IN_PROGRESS": "🟡",
    "TESTING": "🧪",
    "STABILIZING": "🛠️",
    "READY": "➡️",
    "BLOCKED": "⛔",
    "PLANNED": "⬜",
    "RELEASED": "🚀",
    "DEPRECATED": "⚠️",
}

STATUS_LABELS = {
    "COMPLETED": "Completed",
    "IN_PROGRESS": "In Progress",
    "TESTING": "Testing",
    "STABILIZING": "Stabilizing",
    "READY": "Ready",
    "BLOCKED": "Blocked",
    "PLANNED": "Planned",
    "RELEASED": "Released",
    "DEPRECATED": "Deprecated",
}


@dataclass(frozen=True)
class DisplayOptions:
    """Console rendering preferences."""

    emoji: bool = True
    color: bool = True


class Palette:
    """Small ANSI palette with automatic disabling."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def paint(self, text: str, *codes: str) -> str:
        if not self.enabled:
            return text
        return "".join(codes) + text + self.RESET


def _supports_color(no_color: bool) -> bool:
    if no_color or os.environ.get("NO_COLOR") is not None:
        return False
    if not sys.stdout.isatty():
        return False
    return os.name != "nt" or bool(os.environ.get("ANSICON")) or bool(
        os.environ.get("WT_SESSION")
    )


def _icon(name: str, options: DisplayOptions) -> str:
    if not options.emoji:
        return ""
    return STATUS_ICONS.get(name, "•")


def _status_icon(status: str, options: DisplayOptions) -> str:
    if not options.emoji:
        return ""
    return STATUS_ICONS.get(status, "•")


def _separator(character: str = "═", width: int = 72) -> str:
    return character * width


def _percentage(part: int, whole: int) -> float:
    return 0.0 if whole == 0 else (part / whole) * 100.0


def _progress_bar(part: int, whole: int, width: int = BAR_WIDTH) -> str:
    if whole <= 0:
        return "░" * width
    ratio = min(max(part / whole, 0.0), 1.0)
    filled = int(round(ratio * width))
    return "█" * filled + "░" * (width - filled)


def _is_root(record: Mapping[str, object]) -> bool:
    return record["parent_number"] is None


def _records(roots_only: bool = False) -> tuple[Mapping[str, object], ...]:
    source = data.ROOT_MILESTONES if roots_only else data.MILESTONES
    return tuple(source)


def _status_counts(
    records: Iterable[Mapping[str, object]],
) -> Counter[str]:
    return Counter(str(record["status"]) for record in records)


def _completed_count(records: Iterable[Mapping[str, object]]) -> int:
    completed_states = {"COMPLETED", "RELEASED"}
    return sum(1 for record in records if str(record["status"]) in completed_states)


def _active_records() -> tuple[Mapping[str, object], ...]:
    active_states = {"IN_PROGRESS", "TESTING", "STABILIZING"}
    return tuple(
        record for record in data.MILESTONES
        if str(record["status"]) in active_states
    )


def _first_planned_root() -> Mapping[str, object] | None:
    for record in data.ROOT_MILESTONES:
        if str(record["status"]) not in {"COMPLETED", "RELEASED"}:
            return record
    return None


def _current_milestone() -> Mapping[str, object] | None:
    active = _active_records()
    if active:
        roots = [record for record in active if _is_root(record)]
        return roots[0] if roots else active[0]
    return _first_planned_root()


def _next_milestone() -> Mapping[str, object] | None:
    current = _current_milestone()
    if current is None:
        return None

    current_number = str(current["number"])
    if _is_root(current):
        roots = list(data.ROOT_MILESTONES)
        index = next(
            index for index, record in enumerate(roots)
            if str(record["number"]) == current_number
        )
        for candidate in roots[index + 1:]:
            if str(candidate["status"]) not in {"COMPLETED", "RELEASED"}:
                return candidate
        return None

    for record in data.MILESTONES:
        if int(record["sequence"]) > int(current["sequence"]):
            if str(record["status"]) not in {"COMPLETED", "RELEASED"}:
                return record
    return None


def _format_record(
    record: Mapping[str, object],
    options: DisplayOptions,
    palette: Palette,
    indent: bool = False,
) -> str:
    status = str(record["status"])
    prefix = _status_icon(status, options)
    spacing = "  " * int(record["depth"]) if indent else ""
    number = palette.paint(str(record["number"]), Palette.BOLD, Palette.CYAN)
    title = str(record["title"])
    label = STATUS_LABELS.get(status, status.replace("_", " ").title())
    status_text = palette.paint(label, Palette.DIM)
    icon_text = f"{prefix} " if prefix else ""
    return f"{spacing}{icon_text}{number} — {title} [{status_text}]"


def _print_header(
    title: str,
    options: DisplayOptions,
    palette: Palette,
) -> None:
    print(palette.paint(_separator(), Palette.BLUE))
    rocket = "🚀 " if options.emoji else ""
    print(palette.paint(f"{rocket}{title}", Palette.BOLD, Palette.CYAN))
    print(palette.paint(_separator(), Palette.BLUE))


def _print_record_details(
    record: Mapping[str, object],
    options: DisplayOptions,
    palette: Palette,
) -> None:
    print(_format_record(record, options, palette))
    print(f"Record ID          : {record['record_id']}")
    print(f"Sequence           : {record['sequence']}")
    print(f"Hierarchy depth    : {record['depth']}")
    print(f"Parent             : {record['parent_number'] or 'None (root milestone)'}")
    print(f"Priority           : {record['priority']}")
    print(f"Verification       : {record['verification_state']}")
    print(f"Semantic path      : {record['semantic_path']}")
    dependencies = tuple(record["dependencies"])
    print(
        "Dependencies       : "
        + (", ".join(str(item) for item in dependencies) if dependencies else "None")
    )
    print(f"Started date       : {record['started_date'] or 'Not recorded'}")
    print(f"Completed date     : {record['completed_date'] or 'Not recorded'}")
    print(f"Commit hash        : {record['commit_hash'] or 'Not recorded'}")
    print(f"Passing tests      : {record['passing_tests'] if record['passing_tests'] is not None else 'Not recorded'}")


def command_dashboard(
    _args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    all_records = _records()
    root_records = _records(roots_only=True)
    all_counts = _status_counts(all_records)
    root_counts = _status_counts(root_records)

    all_completed = _completed_count(all_records)
    root_completed = _completed_count(root_records)
    all_percent = _percentage(all_completed, len(all_records))
    root_percent = _percentage(root_completed, len(root_records))

    _print_header(data.ROADMAP_TITLE, options, palette)
    print(f"Roadmap version    : {data.ROADMAP_VERSION}")
    print(f"Roadmap range      : {data.ROADMAP_START} → {data.ROADMAP_END}")
    print(f"Root milestones    : {len(root_records)}")
    print(f"All roadmap records: {len(all_records)}")
    print()

    print(palette.paint("Overall record progress", Palette.BOLD))
    print(
        f"{_progress_bar(all_completed, len(all_records))} "
        f"{all_percent:6.2f}%"
    )
    print(
        f"{_icon('COMPLETED', options)} Completed : "
        f"{all_completed}".strip()
    )
    print(
        f"{_icon('IN_PROGRESS', options)} In progress: "
        f"{all_counts.get('IN_PROGRESS', 0)}".strip()
    )
    print(
        f"{_icon('PLANNED', options)} Planned   : "
        f"{all_counts.get('PLANNED', 0)}".strip()
    )
    print(
        f"{_icon('BLOCKED', options)} Blocked   : "
        f"{all_counts.get('BLOCKED', 0)}".strip()
    )
    print()

    print(palette.paint("Major milestone progress", Palette.BOLD))
    print(
        f"{_progress_bar(root_completed, len(root_records))} "
        f"{root_percent:6.2f}%"
    )
    print(
        f"{_icon('COMPLETED', options)} Completed roots: "
        f"{root_completed}".strip()
    )
    print(
        f"{_icon('PLANNED', options)} Remaining roots: "
        f"{len(root_records) - root_completed}".strip()
    )
    print()

    current = _current_milestone()
    upcoming = _next_milestone()
    print(palette.paint("Current milestone", Palette.BOLD))
    if current is None:
        print("🎉 Roadmap complete." if options.emoji else "Roadmap complete.")
    else:
        print(_format_record(current, options, palette))
    print()

    print(palette.paint("Next major milestone", Palette.BOLD))
    if upcoming is None:
        print("None")
    else:
        print(_format_record(upcoming, options, palette))
    print(palette.paint(_separator(), Palette.BLUE))
    return EXIT_OK


def command_progress(
    args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    records = _records(roots_only=args.roots)
    completed = _completed_count(records)
    total = len(records)
    percent = _percentage(completed, total)
    counts = _status_counts(records)

    scope = "major milestones" if args.roots else "all roadmap records"
    _print_header(f"Roadmap Progress — {scope}", options, palette)
    print(f"{_progress_bar(completed, total)} {percent:6.2f}%")
    print(f"Completed : {completed}")
    print(f"Remaining : {total - completed}")
    print(f"Total     : {total}")
    print()
    for status in sorted(counts):
        icon = _status_icon(status, options)
        label = STATUS_LABELS.get(status, status.replace("_", " ").title())
        prefix = f"{icon} " if icon else ""
        print(f"{prefix}{label:<14}: {counts[status]}")
    return EXIT_OK


def command_current(
    _args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    _print_header("Current Milestone", options, palette)
    record = _current_milestone()
    if record is None:
        print("🎉 Every milestone is complete." if options.emoji else "Every milestone is complete.")
        return EXIT_OK
    _print_record_details(record, options, palette)
    return EXIT_OK


def command_next(
    _args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    _print_header("Next Major Milestone", options, palette)
    record = _next_milestone()
    if record is None:
        print("No later incomplete major milestone was found.")
        return EXIT_OK
    _print_record_details(record, options, palette)
    return EXIT_OK


def command_status(
    args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    records = _records(roots_only=args.roots)
    _print_header(
        "Major Milestone Status" if args.roots else "Roadmap Status",
        options,
        palette,
    )
    for record in records:
        print(_format_record(record, options, palette, indent=not args.roots))
    print()
    print(f"Displayed: {len(records)}")
    return EXIT_OK


def _command_list_by_status(
    status: str,
    args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    records = tuple(
        record for record in _records(roots_only=args.roots)
        if str(record["status"]) == status
    )
    title = STATUS_LABELS.get(status, status.title())
    _print_header(f"{title} Milestones", options, palette)
    if not records:
        print("No matching milestones.")
        return EXIT_OK

    limit = args.limit if args.limit is not None else len(records)
    for record in records[:limit]:
        print(_format_record(record, options, palette, indent=not args.roots))
    if limit < len(records):
        print(f"\n… {len(records) - limit} additional matching records not displayed.")
    print(f"\nDisplayed: {min(limit, len(records))} of {len(records)}")
    return EXIT_OK


def command_completed(
    args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    return _command_list_by_status("COMPLETED", args, options, palette)


def command_planned(
    args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    return _command_list_by_status("PLANNED", args, options, palette)


def command_show(
    args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    try:
        record = data.get_milestone(args.number)
    except KeyError as exc:
        print(f"❌ {exc}" if options.emoji else str(exc), file=sys.stderr)
        return EXIT_INVALID

    _print_header(f"Milestone {args.number}", options, palette)
    _print_record_details(record, options, palette)
    children = data.get_children(args.number)
    print(f"Direct children    : {len(children)}")
    print(f"All descendants   : {len(data.get_descendants(args.number))}")
    return EXIT_OK


def command_tree(
    args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    try:
        root = data.get_milestone(args.number)
    except KeyError as exc:
        print(f"❌ {exc}" if options.emoji else str(exc), file=sys.stderr)
        return EXIT_INVALID

    descendants = data.get_descendants(args.number)
    records = (root,) + descendants
    if args.depth is not None:
        maximum_depth = int(root["depth"]) + args.depth
        records = tuple(
            record for record in records
            if int(record["depth"]) <= maximum_depth
        )

    _print_header(f"Roadmap Tree — {args.number}", options, palette)
    base_depth = int(root["depth"])
    for record in records:
        adjusted = dict(record)
        adjusted["depth"] = int(record["depth"]) - base_depth
        print(_format_record(adjusted, options, palette, indent=True))
    print(f"\nDisplayed: {len(records)}")
    return EXIT_OK


def _verify_integrity() -> list[str]:
    errors: list[str] = []
    records = tuple(data.MILESTONES)
    numbers = [str(record["number"]) for record in records]
    record_ids = [str(record["record_id"]) for record in records]
    known_numbers = set(numbers)
    known_ids = set(record_ids)

    if not records:
        errors.append("Roadmap contains no milestone records.")
        return errors

    if numbers[0] != data.ROADMAP_START:
        errors.append(
            f"First milestone is {numbers[0]}, expected {data.ROADMAP_START}."
        )
    if numbers[-1] != data.ROADMAP_END:
        errors.append(
            f"Final milestone is {numbers[-1]}, expected {data.ROADMAP_END}."
        )
    if len(numbers) != len(known_numbers):
        errors.append("Duplicate visible milestone numbers detected.")
    if len(record_ids) != len(known_ids):
        errors.append("Duplicate stable record IDs detected.")

    expected_roots = [f"M{number:03d}" for number in range(1, 23)]
    actual_roots = [
        str(record["number"]) for record in records
        if record["parent_number"] is None
    ]
    if actual_roots != expected_roots:
        errors.append("Root milestones are not sequential from M001 to M022.")

    for expected_sequence, record in enumerate(records, start=1):
        number = str(record["number"])
        if int(record["sequence"]) != expected_sequence:
            errors.append(
                f"{number} has sequence {record['sequence']}; "
                f"expected {expected_sequence}."
            )
        if str(record["status"]) not in data.ALLOWED_STATUSES:
            errors.append(f"{number} uses unsupported status {record['status']!r}.")
        parent = record["parent_number"]
        if parent is not None and str(parent) not in known_numbers:
            errors.append(f"{number} references missing parent {parent}.")
        if int(record["depth"]) != number.count("."):
            errors.append(f"{number} has an incorrect hierarchy depth.")
        if not str(record["record_id"]).startswith("npp-rm-"):
            errors.append(f"{number} has an invalid stable record ID format.")

        for dependency in tuple(record["dependencies"]):
            dependency_text = str(dependency)
            if dependency_text not in known_numbers and dependency_text not in known_ids:
                errors.append(
                    f"{number} references unknown dependency {dependency_text}."
                )

    if data.TOTAL_MILESTONES != len(records):
        errors.append("TOTAL_MILESTONES does not match the milestone collection.")
    if data.COMPLETED_MILESTONES != _completed_count(records):
        errors.append("COMPLETED_MILESTONES does not match calculated status totals.")
    if data.PLANNED_MILESTONES != sum(
        1 for record in records if record["status"] == "PLANNED"
    ):
        errors.append("PLANNED_MILESTONES does not match calculated status totals.")

    return errors


def command_verify(
    _args: argparse.Namespace,
    options: DisplayOptions,
    palette: Palette,
) -> int:
    _print_header("Roadmap Integrity Verification", options, palette)
    errors = _verify_integrity()
    checks = (
        "Roadmap boundaries",
        "Root milestone sequence",
        "Visible milestone uniqueness",
        "Stable record-ID uniqueness",
        "Parent references",
        "Hierarchy depths",
        "Sequence values",
        "Allowed statuses",
        "Dependency references",
        "Summary count constants",
    )

    if errors:
        print(
            palette.paint(
                f"{_icon('BLOCKED', options)} Verification failed with "
                f"{len(errors)} error(s).".strip(),
                Palette.BOLD,
                Palette.RED,
            )
        )
        for error in errors:
            print(f"  - {error}")
        return EXIT_INVALID

    print(
        palette.paint(
            f"{_icon('COMPLETED', options)} All integrity checks passed.".strip(),
            Palette.BOLD,
            Palette.GREEN,
        )
    )
    print()
    for check in checks:
        prefix = "✅ " if options.emoji else ""
        print(f"{prefix}{check}")
    print()
    print(f"Verified records : {data.TOTAL_MILESTONES}")
    print(f"Verified roots   : {len(data.ROOT_MILESTONES)}")
    print(f"Roadmap range    : {data.ROADMAP_START} → {data.ROADMAP_END}")
    return EXIT_OK


def command_json(
    args: argparse.Namespace,
    _options: DisplayOptions,
    _palette: Palette,
) -> int:
    if args.number:
        try:
            payload: object = dict(data.get_milestone(args.number))
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return EXIT_INVALID
    elif args.roots:
        payload = [dict(record) for record in data.ROOT_MILESTONES]
    elif args.summary:
        payload = dict(data.roadmap_summary())
    else:
        payload = [dict(record) for record in data.MILESTONES]

    print(json.dumps(payload, indent=2, ensure_ascii=False, default=list))
    return EXIT_OK


def _add_list_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--roots",
        action="store_true",
        help="Show only major/root milestones.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of matching records to display.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roadmap.py",
        description="Nexa Provider Platform roadmap dashboard and verifier.",
    )
    parser.add_argument(
        "--no-emoji",
        action="store_true",
        help="Disable emoji symbols.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI terminal colors.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {data.ROADMAP_VERSION}",
    )

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("dashboard", help="Show the main roadmap dashboard.")

    progress = subparsers.add_parser("progress", help="Show progress counts.")
    progress.add_argument(
        "--roots",
        action="store_true",
        help="Calculate progress using only major/root milestones.",
    )

    subparsers.add_parser("current", help="Show the current milestone.")
    subparsers.add_parser("next", help="Show the next major milestone.")

    status = subparsers.add_parser("status", help="List milestone statuses.")
    status.add_argument(
        "--roots",
        action="store_true",
        help="Show only major/root milestones.",
    )

    completed = subparsers.add_parser(
        "completed",
        help="List completed milestones.",
    )
    _add_list_arguments(completed)

    planned = subparsers.add_parser(
        "planned",
        help="List planned milestones.",
    )
    _add_list_arguments(planned)

    show = subparsers.add_parser("show", help="Show one milestone in detail.")
    show.add_argument("number", help="Milestone number, for example M012.6.")

    tree = subparsers.add_parser(
        "tree",
        help="Show a milestone and its descendants.",
    )
    tree.add_argument("number", help="Milestone number, for example M012.6.")
    tree.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Maximum descendant levels to display.",
    )

    subparsers.add_parser("verify", help="Run roadmap integrity checks.")

    json_parser = subparsers.add_parser(
        "json",
        help="Print roadmap information as JSON.",
    )
    json_group = json_parser.add_mutually_exclusive_group()
    json_group.add_argument(
        "--summary",
        action="store_true",
        help="Print only the roadmap summary.",
    )
    json_group.add_argument(
        "--roots",
        action="store_true",
        help="Print only major/root milestones.",
    )
    json_group.add_argument(
        "--number",
        help="Print one milestone by visible number.",
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    options = DisplayOptions(
        emoji=not args.no_emoji,
        color=_supports_color(args.no_color),
    )
    palette = Palette(options.color)

    command = args.command or "dashboard"
    handlers = {
        "dashboard": command_dashboard,
        "progress": command_progress,
        "current": command_current,
        "next": command_next,
        "status": command_status,
        "completed": command_completed,
        "planned": command_planned,
        "show": command_show,
        "tree": command_tree,
        "verify": command_verify,
        "json": command_json,
    }

    handler = handlers.get(command)
    if handler is None:
        parser.error(f"Unknown command: {command}")
    return handler(args, options, palette)


if __name__ == "__main__":
    raise SystemExit(main())
