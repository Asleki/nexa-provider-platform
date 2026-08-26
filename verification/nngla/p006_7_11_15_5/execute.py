#!/usr/bin/env python3
"""Explicit governed write runner for one approved .15.5 city-root selection."""
from __future__ import annotations

import argparse
import json

from registries.nngla.spatial_realization.orchestration import GovernedSpatialBatchEngine
from registries.nngla.spatial_realization.persistence import PostgreSQLSpatialRealizationRepository
from registries.nngla.spatial_realization.topology import PostGISSpatialTopologyEngine

from verification.nngla.p006_7_11_15_5.common import connect_postgresql, effective_date, repair_mode, repository_revision, selected_roots


def parser() -> argparse.ArgumentParser:
    value = argparse.ArgumentParser(description=__doc__)
    value.add_argument("--roots", nargs="+", required=True, help="Canonical NG-PLC major-city root IDs from the approved preview")
    value.add_argument("--repair-mode", default="safe-automatic", choices=("disabled", "safe-automatic", "governed-structural"))
    value.add_argument("--environment-name", default="dev")
    value.add_argument("--effective-date", required=True, help="Exact effectiveDate from the approved preview (YYYY-MM-DD)")
    value.add_argument("--repository-revision", default="")
    value.add_argument("--approved-fingerprint", required=True)
    value.add_argument("--confirmation", required=True)
    value.add_argument("--submitter", required=True)
    value.add_argument("--approver", required=True)
    value.add_argument("--execute", action="store_true", help="Required explicit write acknowledgement")
    return value


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    if not args.execute:
        raise SystemExit("REFUSED: --execute is required after reviewing a fresh read-only preview")
    roots = selected_roots(roots=args.roots, all_cities=False)
    revision = args.repository_revision.strip() or repository_revision()
    connection = connect_postgresql()
    try:
        repository = PostgreSQLSpatialRealizationRepository(connection, environment_name=args.environment_name, effective_date=effective_date(args.effective_date))
        topology = PostGISSpatialTopologyEngine(connection, repair_mode=repair_mode(args.repair_mode))
        engine = GovernedSpatialBatchEngine(repository, topology, repository_revision=revision)
        receipt = engine.execute(
            roots,
            approved_fingerprint=args.approved_fingerprint,
            confirmation=args.confirmation,
            submitter_actor_id=args.submitter,
            approver_actor_id=args.approver,
        )
        print(json.dumps({
            "executionId": receipt.execution_id,
            "fingerprint": receipt.fingerprint_sha256,
            "databaseName": receipt.database_name,
            "environmentName": receipt.environment_name,
            "repositoryRevision": receipt.repository_revision,
            "effectiveDate": args.effective_date,
            "selectedRootCount": receipt.selected_root_count,
            "geometryInsertCount": receipt.geometry_insert_count,
            "associationCount": receipt.association_count,
            "reusedCount": receipt.reused_count,
            "status": receipt.status,
            "replayed": receipt.replayed,
        }, indent=2, sort_keys=True))
        return 0
    finally:
        connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
