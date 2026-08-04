#!/usr/bin/env python3
"""Terminal dashboard and integrity verifier for the NexiLabs PWA roadmap."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from typing import Mapping, Sequence

import pwa_roadmap_data as data

EXIT_OK = 0
EXIT_INVALID = 2
COMPLETED_STATES = {"COMPLETED", "RELEASED"}


def percentage(part: int, whole: int) -> float:
    return 0.0 if whole == 0 else part / whole * 100.0


def progress_bar(part: int, whole: int, width: int = 30) -> str:
    filled = 0 if whole == 0 else round((part / whole) * width)
    return "█" * filled + "░" * (width - filled)


def completed_count(records) -> int:
    return sum(str(item["status"]) in COMPLETED_STATES for item in records)


def current_record():
    for item in data.MILESTONES:
        if str(item["status"]) not in COMPLETED_STATES:
            return item
    return None


def format_record(item: Mapping[str, object], indent: bool = False) -> str:
    icon = "✅" if item["status"] == "COMPLETED" else "🟦"
    prefix = "  " * int(item["depth"]) if indent else ""
    return f"{prefix}{icon} {item['number']} — {item['title']} [{item['status']}]"


def verify_integrity() -> list[str]:
    errors: list[str] = []
    records = tuple(data.MILESTONES)
    numbers = [str(item["number"]) for item in records]
    ids = [str(item["record_id"]) for item in records]
    known_numbers = set(numbers)
    known_ids = set(ids)

    if not records:
        return ["Roadmap contains no records."]
    if numbers[0] != data.ROADMAP_START:
        errors.append(f"First record is {numbers[0]}, expected {data.ROADMAP_START}.")
    if numbers[-1] != data.ROADMAP_END:
        errors.append(f"Final record is {numbers[-1]}, expected {data.ROADMAP_END}.")
    if len(numbers) != len(known_numbers):
        errors.append("Duplicate visible milestone numbers detected.")
    if len(ids) != len(known_ids):
        errors.append("Duplicate stable record IDs detected.")

    roots = [str(item["number"]) for item in records if item["parent_number"] is None]
    expected_roots = [f"P{number:03d}" for number in range(1, len(roots) + 1)]
    if roots != expected_roots:
        errors.append(
            f"Root sequence mismatch: expected {expected_roots}, found {roots}."
        )

    for sequence, item in enumerate(records, start=1):
        number = str(item["number"])
        if int(item["sequence"]) != sequence:
            errors.append(f"{number} has sequence {item['sequence']}; expected {sequence}.")
        if str(item["status"]) not in data.ALLOWED_STATUSES:
            errors.append(f"{number} has unsupported status {item['status']!r}.")
        parent = item["parent_number"]
        if parent is not None and str(parent) not in known_numbers:
            errors.append(f"{number} references missing parent {parent}.")
        if int(item["depth"]) != number.count("."):
            errors.append(f"{number} has incorrect hierarchy depth.")
        if not str(item["record_id"]).startswith("nxl-pwa-rm-"):
            errors.append(f"{number} has invalid stable record ID prefix.")
        for dependency in tuple(item["dependencies"]):
            if str(dependency) not in known_numbers and str(dependency) not in known_ids:
                errors.append(f"{number} references unknown dependency {dependency}.")

    if data.TOTAL_MILESTONES != len(records):
        errors.append("TOTAL_MILESTONES does not match the collection.")
    if data.COMPLETED_MILESTONES != completed_count(records):
        errors.append("COMPLETED_MILESTONES does not match calculated totals.")
    if data.PLANNED_MILESTONES != sum(item["status"] == "PLANNED" for item in records):
        errors.append("PLANNED_MILESTONES does not match calculated totals.")
    return errors


def dashboard() -> int:
    completed = completed_count(data.MILESTONES)
    total = len(data.MILESTONES)
    print("=" * 76)
    print(data.ROADMAP_TITLE)
    print("=" * 76)
    print(f"Version           : {data.ROADMAP_VERSION}")
    print(f"Range             : {data.ROADMAP_START} → {data.ROADMAP_END}")
    print(f"Root milestones   : {len(data.ROOT_MILESTONES)}")
    print(f"Canonical records : {total}")
    print(f"Progress          : {progress_bar(completed, total)} {percentage(completed,total):.2f}%")
    print(f"Completed         : {completed}")
    print(f"Planned           : {data.PLANNED_MILESTONES}")
    current = current_record()
    print(f"Current           : {current['number'] + ' — ' + current['title'] if current else 'Roadmap complete'}")
    print("=" * 76)
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="pwa_roadmap.py")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("dashboard")
    sub.add_parser("progress")
    sub.add_parser("current")
    sub.add_parser("next")
    status = sub.add_parser("status")
    status.add_argument("--roots", action="store_true")
    show = sub.add_parser("show")
    show.add_argument("number")
    tree = sub.add_parser("tree")
    tree.add_argument("number")
    sub.add_parser("verify")
    js = sub.add_parser("json")
    js.add_argument("--summary", action="store_true")
    args = parser.parse_args(argv)
    command = args.command or "dashboard"

    if command == "dashboard":
        return dashboard()
    if command == "progress":
        completed = completed_count(data.MILESTONES)
        print(f"{completed}/{len(data.MILESTONES)} ({percentage(completed,len(data.MILESTONES)):.2f}%)")
        return EXIT_OK
    if command in {"current", "next"}:
        item = current_record()
        print(format_record(item) if item else "Roadmap complete.")
        return EXIT_OK
    if command == "status":
        records = data.ROOT_MILESTONES if args.roots else data.MILESTONES
        for item in records:
            print(format_record(item, indent=not args.roots))
        return EXIT_OK
    if command == "show":
        try:
            item = data.get_milestone(args.number)
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return EXIT_INVALID
        print(json.dumps(dict(item), indent=2, ensure_ascii=False, default=list))
        return EXIT_OK
    if command == "tree":
        try:
            root = data.get_milestone(args.number)
        except KeyError as exc:
            print(str(exc), file=sys.stderr)
            return EXIT_INVALID
        for item in (root,) + data.get_descendants(args.number):
            adjusted = dict(item)
            adjusted["depth"] = int(item["depth"]) - int(root["depth"])
            print(format_record(adjusted, indent=True))
        return EXIT_OK
    if command == "verify":
        errors = verify_integrity()
        if errors:
            print(f"Verification failed with {len(errors)} error(s).")
            for error in errors:
                print(f"- {error}")
            return EXIT_INVALID
        print("All PWA roadmap integrity checks passed.")
        print(f"Verified records: {data.TOTAL_MILESTONES}")
        print(f"Verified roots  : {len(data.ROOT_MILESTONES)}")
        print(f"Roadmap range   : {data.ROADMAP_START} → {data.ROADMAP_END}")
        return EXIT_OK
    if command == "json":
        if args.summary:
            payload = dict(data.roadmap_summary())
        else:
            payload = [dict(item) for item in data.MILESTONES]

        print(
            json.dumps(
                payload,
                indent=2,
                ensure_ascii=False,
                default=list,
            )
        )
        return EXIT_OK
    parser.error(f"Unknown command: {command}")
    return EXIT_INVALID


if __name__ == "__main__":
    raise SystemExit(main())
