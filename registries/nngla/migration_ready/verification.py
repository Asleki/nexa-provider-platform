"""Final live PostgreSQL verification for NNGLA Migration Ready."""
from __future__ import annotations

from math import isclose
from pathlib import Path

from registries.nngla.spatial_fabric.bundle17e.canonical import canonical_by_candidate
from registries.nngla.spatial_fabric.bundle17e.geometry import geometry_by_candidate
from registries.nngla.spatial_fabric.bundle17e.persistence import PostgreSQLSpatialRepository

from .baseline import verify_immutable_baseline
from .candidate_state import assess_candidate_state
from .contracts import ReconciliationAction, VerificationReport
from .empty_registers import assess_empty_registers, empty_registers_ready
from .orchestrator import PLAN_ID
from .reconciliation import reconcile_spatial_target

BUNDLE17E_PLAN_ID = "P006.7.11.7.7-8-BUNDLE17E"


def _geometry_content_findings(connection, expected_geometries) -> tuple[str, ...]:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT v.geometry_id,v.subject_id,ST_X(v.geometry),ST_Y(v.geometry),ST_SRID(v.geometry),"
            "a.checksum_sha256 FROM geography.nngla_geometry_version v "
            "JOIN geography.nngla_geometry_authority_record a ON a.geometry_id=v.geometry_id "
            "WHERE v.geometry_role_code='SPATIAL_REFERENCE_POINT' AND v.runtime_mode='production' "
            "AND v.valid_to IS NULL"
        )
        actual = {
            str(row[0]): (str(row[1]), float(row[2]), float(row[3]), int(row[4]), str(row[5]))
            for row in cur.fetchall()
        }
    findings: list[str] = []
    for geometry in expected_geometries.values():
        row = actual.get(geometry.geometry_id)
        if row is None:
            findings.append(f"GEOMETRY_CONTENT_MISSING:{geometry.geometry_id}")
            continue
        subject_id, lon, lat, srid, checksum = row
        if subject_id != geometry.canonical_spatial_point_id:
            findings.append(f"GEOMETRY_SUBJECT_MISMATCH:{geometry.geometry_id}")
        if srid != 4326:
            findings.append(f"GEOMETRY_SRID_MISMATCH:{geometry.geometry_id}:{srid}")
        if not isclose(lon, float(geometry.longitude), rel_tol=0.0, abs_tol=1e-10):
            findings.append(f"GEOMETRY_LONGITUDE_MISMATCH:{geometry.geometry_id}")
        if not isclose(lat, float(geometry.latitude), rel_tol=0.0, abs_tol=1e-10):
            findings.append(f"GEOMETRY_LATITUDE_MISMATCH:{geometry.geometry_id}")
        if checksum != geometry.geometry_payload_sha256:
            findings.append(f"GEOMETRY_CHECKSUM_MISMATCH:{geometry.geometry_id}")
    return tuple(findings)


def _receipt_item_count(connection) -> int:
    with connection.cursor() as cur:
        cur.execute(
            "SELECT count(DISTINCT i.source_record_id) "
            "FROM geography.nngla_execution_item i "
            "JOIN geography.nngla_execution_receipt r ON r.execution_id=i.execution_id "
            "WHERE r.plan_id IN (%s,%s) AND i.outcome IN ('INSERTED','REUSED')",
            (BUNDLE17E_PLAN_ID, PLAN_ID),
        )
        return int(cur.fetchone()[0])


def verify_migration_ready(
    root: Path,
    connection,
    *,
    database_name: str,
    environment_name: str,
) -> VerificationReport:
    crosswalks = canonical_by_candidate()
    geometries = geometry_by_candidate()
    repository = PostgreSQLSpatialRepository(connection)
    target = repository.snapshot(database_name, environment_name)
    reconciliation = reconcile_spatial_target(target, crosswalks, geometries)

    expected_ids = set(crosswalks)
    expected_items = [item for item in reconciliation if item.coordinate_candidate_id in expected_ids]
    missing = tuple(
        item.coordinate_candidate_id
        for item in expected_items
        if item.action is ReconciliationAction.INSERT_NEW
    )
    conflicts = tuple(
        item.coordinate_candidate_id
        for item in reconciliation
        if item.action is ReconciliationAction.CONFLICT
    )
    reused = sum(1 for item in expected_items if item.action is ReconciliationAction.REUSE_CANONICAL)

    empty = assess_empty_registers(root, connection)
    baseline = verify_immutable_baseline(root, connection)
    candidate = assess_candidate_state(root)
    findings = list(_geometry_content_findings(connection, geometries))
    receipt_count = _receipt_item_count(connection)
    if receipt_count != 2411:
        findings.append(f"SPATIAL_RECEIPT_ITEM_COVERAGE:{receipt_count}:EXPECTED=2411")

    baseline_findings = tuple(
        list(baseline.findings)
        + [f"BASELINE_MISSING:{value}" for value in baseline.missing]
        + [f"BASELINE_CONFLICT:{value}" for value in baseline.conflicts]
    )
    candidate_findings = candidate.findings if candidate.passed else (
        candidate.findings or ("CANDIDATE_STATE_NOT_LOCKED",)
    )

    return VerificationReport(
        database_name=database_name,
        expected_spatial_count=2411,
        canonical_count=reused,
        geometry_count=reused,
        crosswalk_count=reused,
        receipt_item_count=receipt_count,
        missing_candidate_ids=missing,
        conflicting_candidate_ids=conflicts,
        empty_registers_ready=empty_registers_ready(empty),
        immutable_baseline_findings=baseline_findings,
        candidate_state_findings=tuple(candidate_findings),
        findings=tuple(findings),
    )


__all__ = ["BUNDLE17E_PLAN_ID", "verify_migration_ready"]
