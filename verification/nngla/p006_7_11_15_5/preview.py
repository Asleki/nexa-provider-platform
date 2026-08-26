#!/usr/bin/env python3
"""Read-only live preview for selected NoveGeo major-city spatial realization."""
from __future__ import annotations

import argparse

from registries.nngla.spatial_realization.orchestration import GovernedSpatialBatchEngine
from registries.nngla.spatial_realization.persistence import PostgreSQLSpatialRealizationRepository
from registries.nngla.spatial_realization.topology import PostGISSpatialTopologyEngine

from verification.nngla.p006_7_11_15_5.common import (
    connect_postgresql,
    effective_date,
    preview_payload,
    repair_mode,
    repository_revision,
    selected_roots,
    write_json,
)


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    group = value.add_mutually_exclusive_group(required=True)
    group.add_argument("--roots", nargs="+", help="Canonical NG-PLC major-city root IDs")
    group.add_argument("--all-cities", action="store_true", help="Assess all eight major-city roots in one read-only preview")
    value.add_argument("--repair-mode", default="safe-automatic", choices=("disabled", "safe-automatic", "governed-structural"))
    value.add_argument("--environment-name", default="dev")
    value.add_argument("--effective-date", default="", help="Governed geometry effective date YYYY-MM-DD; defaults to today")
    value.add_argument("--repository-revision", default="")
    value.add_argument("--output", default="", help="Optional JSON report path")
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    roots = selected_roots(roots=args.roots, all_cities=args.all_cities)
    revision = args.repository_revision.strip() or repository_revision()
    connection = connect_postgresql()
    try:
        with connection.transaction():
            connection.execute("SET TRANSACTION READ ONLY")
            repository = PostgreSQLSpatialRealizationRepository(connection, environment_name=args.environment_name, effective_date=effective_date(args.effective_date or None))
            topology = PostGISSpatialTopologyEngine(connection, repair_mode=repair_mode(args.repair_mode))
            engine = GovernedSpatialBatchEngine(repository, topology, repository_revision=revision)
            preview = engine.preview(roots)
            payload = preview_payload(preview)
        write_json(payload, args.output or None)
        return 0 if preview.execution_ready else 2
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
