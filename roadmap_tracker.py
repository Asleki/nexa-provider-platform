#!/usr/bin/env python3
"""
NPP Architecture + Tracker documentation build pipeline.

This is the only new root-level orchestration logic. It calls existing
architecture functions without modifying their files or canonical data.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from roadmap.models import RoadmapMetadata, RoadmapSnapshot, milestones_from_mappings
from roadmap.validation import validate_roadmap
from roadmap.tracker.architecture import ArchitectureSnapshot
from roadmap.tracker.engine import TrackerEngine
from roadmap.tracker.storage import TrackerStore

import roadmap_data
import roadmap_frontend


DEFAULT_TRACKER_DATA = Path("roadmap/tracker/data/tracker_records.json")
DEFAULT_ROADMAP_OUTPUT = Path("ROADMAP.md")
DEFAULT_TRACKER_OUTPUT = Path("ROADMAP_TRACKER.md")


class DocumentationPipelineError(RuntimeError):
    pass


def build_architecture_snapshot() -> RoadmapSnapshot:
    metadata = RoadmapMetadata(
        title=roadmap_data.ROADMAP_TITLE,
        version=roadmap_data.ROADMAP_VERSION,
        start=roadmap_data.ROADMAP_START,
        end=roadmap_data.ROADMAP_END,
        allowed_statuses=tuple(roadmap_data.ALLOWED_STATUSES),
        boundaries=getattr(roadmap_data, "ROADMAP_BOUNDARIES", {}),
    )
    return RoadmapSnapshot(
        metadata=metadata,
        milestones=milestones_from_mappings(roadmap_data.MILESTONES),
    )


def run_pipeline(
    *,
    tracker_data: Path = DEFAULT_TRACKER_DATA,
    roadmap_output: Path = DEFAULT_ROADMAP_OUTPUT,
    tracker_output: Path = DEFAULT_TRACKER_OUTPUT,
) -> int:
    print("1. Validate architecture roadmap")
    snapshot = build_architecture_snapshot()
    report = validate_roadmap(snapshot)
    if not report.is_valid:
        raise DocumentationPipelineError(
            f"architecture validation failed: {report.error_count} error(s)"
        )
    print("   ✓ Architecture valid")

    print("2. Generate ROADMAP.md")
    roadmap_frontend.write_roadmap(roadmap_output)
    print(f"   ✓ Generated {roadmap_output}")

    print("3. Load the newly updated architecture snapshot")
    architecture = ArchitectureSnapshot.from_roadmap(snapshot)
    print(f"   ✓ Snapshot {architecture.sha256[:16]}…")

    print("4. Recalculate tracker architecture progress")
    engine = TrackerEngine(TrackerStore(tracker_data))
    print(
        f"   ✓ Architecture progress "
        f"{architecture.completed}/{len(architecture.records)} "
        f"({architecture.percentage:.2f}%)"
    )

    print("5. Generate ROADMAP_TRACKER.md")
    result = engine.build(
        architecture,
        roadmap_path=roadmap_output,
        output=tracker_output,
    )
    print(f"   ✓ Generated {result.output}")

    print("6. Validate both outputs are synchronized")
    result.validation.raise_for_errors()
    print("   ✓ ROADMAP.md and ROADMAP_TRACKER.md synchronized")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build synchronized NPP architecture and tracker frontends."
    )
    parser.add_argument("--tracker-data", type=Path, default=DEFAULT_TRACKER_DATA)
    parser.add_argument("--roadmap-output", type=Path, default=DEFAULT_ROADMAP_OUTPUT)
    parser.add_argument("--tracker-output", type=Path, default=DEFAULT_TRACKER_OUTPUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return run_pipeline(
            tracker_data=args.tracker_data,
            roadmap_output=args.roadmap_output,
            tracker_output=args.tracker_output,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
