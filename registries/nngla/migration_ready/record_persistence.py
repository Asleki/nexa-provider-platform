"""Additive record-atomic persistence helpers over locked Bundle 17E."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime

from registries.nngla.spatial_fabric.bundle17e._shared import (
    EFFECT_SCOPE,
    RUNTIME_MODE,
    SPATIAL_DATASET_ID,
    SPATIAL_DATASET_VERSION,
)

from .contracts import ReconciliationAction, ReconciliationItem
from .record_contracts import RecordReceiptObservation


def _parse_detail(detail: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for part in str(detail or "").split(";"):
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        values[key.strip()] = value.strip()
    return values


class RecordAtomicPersistence:
    """Record-level durability without changing locked Bundle 17E adapters.

    PostgreSQL commits/rolls back one coordinate at a time.  If a socket is
    already dead, a failed rollback must not hide the original operation error;
    the server will discard the uncommitted transaction with the dead session.
    """

    def __init__(self, repository) -> None:
        self.repository = repository

    @contextmanager
    def transaction(self):
        connection = getattr(self.repository, "connection", None)
        if connection is None:
            with self.repository.transaction():
                yield self.repository
            return
        try:
            yield self.repository
            connection.commit()
        except Exception:
            try:
                connection.rollback()
            except Exception:
                pass
            raise

    def snapshot(self, database_name: str, environment_name: str):
        try:
            return self.repository.snapshot(database_name, environment_name)
        except TypeError:
            return self.repository.snapshot()

    def ensure_source_contract(self, source_sha256: str, source_path: str, row_count: int, byte_size: int) -> None:
        if not hasattr(self.repository, "ensure_source_contract"):
            return
        with self.transaction() as base:
            base.ensure_source_contract(source_sha256, source_path, row_count, byte_size)

    @staticmethod
    def _classify_from_snapshot(snapshot, crosswalk, geometry) -> ReconciliationItem:
        candidate_id = crosswalk.coordinate_candidate_id
        canonical_id = crosswalk.canonical_spatial_point_id
        geometry_id = geometry.geometry_id
        occupied_spatial = set(getattr(snapshot, "occupied_spatial_ids", ()))
        occupied_geometry = set(getattr(snapshot, "occupied_geometry_ids", ()))
        target_crosswalks = dict(getattr(snapshot, "candidate_crosswalks", {}) or {})
        geometry_by_subject = dict(getattr(snapshot, "geometry_by_subject", {}) or {})
        mapped_id = target_crosswalks.get(candidate_id)
        active_geometry_id = geometry_by_subject.get(canonical_id)
        canonical_occupied = canonical_id in occupied_spatial
        geometry_occupied = geometry_id in occupied_geometry

        if mapped_id is not None:
            if mapped_id != canonical_id:
                action, reason = ReconciliationAction.CONFLICT, "CROSSWALK_CANONICAL_ID_MISMATCH"
            elif not canonical_occupied:
                action, reason = ReconciliationAction.CONFLICT, "CROSSWALK_POINTS_TO_MISSING_CANONICAL_FEATURE"
            elif active_geometry_id != geometry_id:
                action, reason = ReconciliationAction.CONFLICT, "ACTIVE_GEOMETRY_MISMATCH"
            elif not geometry_occupied:
                action, reason = ReconciliationAction.CONFLICT, "GEOMETRY_MAPPING_POINTS_TO_MISSING_GEOMETRY"
            else:
                action, reason = ReconciliationAction.REUSE_CANONICAL, "EXACT_POSTGRESQL_STATE_MATCH"
        else:
            if canonical_occupied:
                action, reason = ReconciliationAction.CONFLICT, "CANONICAL_ID_OCCUPIED_WITHOUT_EXPECTED_CROSSWALK"
            elif active_geometry_id is not None:
                action, reason = ReconciliationAction.CONFLICT, "SUBJECT_HAS_UNEXPECTED_ACTIVE_GEOMETRY"
            elif geometry_occupied:
                action, reason = ReconciliationAction.CONFLICT, "GEOMETRY_ID_ALREADY_OCCUPIED"
            else:
                action, reason = ReconciliationAction.INSERT_NEW, "TARGET_IDENTITIES_AVAILABLE"
        return ReconciliationItem(candidate_id, canonical_id, geometry_id, action, reason)

    def classify_record(self, *, database_name: str, environment_name: str, crosswalk, geometry) -> ReconciliationItem:
        connection = getattr(self.repository, "connection", None)
        if connection is None:
            return self._classify_from_snapshot(self.snapshot(database_name, environment_name), crosswalk, geometry)

        candidate_id = crosswalk.coordinate_candidate_id
        canonical_id = crosswalk.canonical_spatial_point_id
        geometry_id = geometry.geometry_id
        with connection.cursor() as cur:
            cur.execute(
                "SELECT "
                "(SELECT canonical_id FROM geography.nngla_canonical_crosswalk "
                " WHERE dataset_id=%s AND dataset_version=%s AND candidate_id=%s AND runtime_mode=%s AND effect_scope=%s LIMIT 1),"
                "EXISTS(SELECT 1 FROM geography.nngla_spatial_feature WHERE feature_id=%s AND record_family='SPATIAL_REFERENCE_POINT'),"
                "(SELECT geometry_id FROM geography.nngla_geometry_version "
                " WHERE subject_id=%s AND geometry_role_code='SPATIAL_REFERENCE_POINT' AND runtime_mode=%s AND valid_to IS NULL LIMIT 1),"
                "EXISTS(SELECT 1 FROM geography.nngla_geometry_authority_record WHERE geometry_id=%s)",
                (
                    SPATIAL_DATASET_ID,
                    SPATIAL_DATASET_VERSION,
                    candidate_id,
                    RUNTIME_MODE,
                    EFFECT_SCOPE,
                    canonical_id,
                    canonical_id,
                    RUNTIME_MODE,
                    geometry_id,
                ),
            )
            mapped_id, canonical_occupied, active_geometry_id, geometry_occupied = cur.fetchone()
        snapshot = type(
            "SingleRecordSnapshot",
            (),
            {
                "occupied_spatial_ids": frozenset({canonical_id} if canonical_occupied else ()),
                "occupied_geometry_ids": frozenset({geometry_id} if geometry_occupied else ()),
                "candidate_crosswalks": {candidate_id: str(mapped_id)} if mapped_id is not None else {},
                "geometry_by_subject": {canonical_id: str(active_geometry_id)} if active_geometry_id is not None else {},
            },
        )()
        return self._classify_from_snapshot(snapshot, crosswalk, geometry)

    def persist_point(self, crosswalk, geometry) -> str:
        return self.repository.persist_point(crosswalk, geometry)

    def persist_execution_receipt(self, receipt) -> None:
        self.repository.persist_execution_receipt(receipt)

    def record_receipt_observations(
        self,
        *,
        plan_id: str,
        plan_version: int,
        database_name: str,
        environment_name: str,
    ) -> tuple[RecordReceiptObservation, ...]:
        if hasattr(self.repository, "receipts"):
            observations: list[RecordReceiptObservation] = []
            for receipt in self.repository.receipts:
                if receipt.plan_id != plan_id or receipt.plan_version != plan_version:
                    continue
                if receipt.database_name != database_name or receipt.environment_name != environment_name:
                    continue
                for item in receipt.items:
                    metadata = _parse_detail(item.detail)
                    required = {
                        "logical_batch_id",
                        "window_start_ordinal",
                        "window_end_ordinal",
                        "requested_count",
                        "migration_ordinal",
                    }
                    if not required.issubset(metadata):
                        continue
                    observations.append(
                        RecordReceiptObservation(
                            execution_id=receipt.execution_id,
                            logical_batch_id=metadata["logical_batch_id"],
                            window_start_ordinal=int(metadata["window_start_ordinal"]),
                            window_end_ordinal=int(metadata["window_end_ordinal"]),
                            requested_count=int(metadata["requested_count"]),
                            migration_ordinal=int(metadata["migration_ordinal"]),
                            coordinate_candidate_id=item.coordinate_candidate_id,
                            canonical_spatial_point_id=item.canonical_spatial_point_id,
                            geometry_id=item.geometry_id,
                            outcome=item.outcome,
                            completed_at=receipt.completed_at,
                        )
                    )
            return tuple(observations)

        connection = getattr(self.repository, "connection", None)
        if connection is None:
            return ()
        with connection.cursor() as cur:
            cur.execute(
                "SELECT r.execution_id,r.completed_at,i.source_record_id,i.canonical_id,i.outcome,"
                "i.detail->>'geometry_id',i.detail->>'detail' "
                "FROM geography.nngla_execution_receipt r "
                "JOIN geography.nngla_execution_item i ON i.execution_id=r.execution_id "
                "WHERE r.plan_id=%s AND r.plan_version=%s AND r.database_name=%s AND r.environment_name=%s "
                "ORDER BY r.completed_at,r.execution_id,i.source_record_id",
                (plan_id, plan_version, database_name, environment_name),
            )
            rows = cur.fetchall()
        observations = []
        for execution_id, completed_at, source_record_id, canonical_id, outcome, geometry_id, detail in rows:
            metadata = _parse_detail(str(detail or ""))
            required = {
                "logical_batch_id",
                "window_start_ordinal",
                "window_end_ordinal",
                "requested_count",
                "migration_ordinal",
            }
            if not required.issubset(metadata):
                continue
            observations.append(
                RecordReceiptObservation(
                    execution_id=str(execution_id),
                    logical_batch_id=metadata["logical_batch_id"],
                    window_start_ordinal=int(metadata["window_start_ordinal"]),
                    window_end_ordinal=int(metadata["window_end_ordinal"]),
                    requested_count=int(metadata["requested_count"]),
                    migration_ordinal=int(metadata["migration_ordinal"]),
                    coordinate_candidate_id=str(source_record_id),
                    canonical_spatial_point_id=str(canonical_id),
                    geometry_id=str(geometry_id),
                    outcome=str(outcome),
                    completed_at=str(completed_at),
                )
            )
        return tuple(observations)

    def record_history(
        self,
        *,
        plan_id: str,
        database_name: str,
        environment_name: str,
        start_ordinal: int | None = None,
        count: int | None = None,
    ) -> tuple[dict, ...]:
        connection = getattr(self.repository, "connection", None)
        if connection is None:
            rows: list[dict] = []
            for receipt in getattr(self.repository, "receipts", ()):
                if receipt.plan_id != plan_id or receipt.database_name != database_name or receipt.environment_name != environment_name:
                    continue
                for item in receipt.items:
                    try:
                        ordinal = int(item.canonical_spatial_point_id.rsplit("-", 1)[1])
                    except Exception:
                        continue
                    rows.append(
                        {
                            "migration_ordinal": ordinal,
                            "canonical_spatial_point_id": item.canonical_spatial_point_id,
                            "geometry_id": item.geometry_id,
                            "execution_id": receipt.execution_id,
                            "plan_version": receipt.plan_version,
                            "outcome": item.outcome,
                            "started_at": receipt.started_at,
                            "completed_at": receipt.completed_at,
                            "runtime_ms": int((datetime.fromisoformat(receipt.completed_at) - datetime.fromisoformat(receipt.started_at)).total_seconds() * 1000),
                            "logical_batch_id": _parse_detail(item.detail).get("logical_batch_id"),
                        }
                    )
        else:
            with connection.cursor() as cur:
                cur.execute(
                    "SELECT i.canonical_id,i.detail->>'geometry_id',r.execution_id,r.plan_version,i.outcome,r.started_at,r.completed_at,"
                    "i.detail->>'detail' "
                    "FROM geography.nngla_execution_receipt r "
                    "JOIN geography.nngla_execution_item i ON i.execution_id=r.execution_id "
                    "WHERE r.plan_id=%s AND r.database_name=%s AND r.environment_name=%s "
                    "ORDER BY i.canonical_id,r.completed_at",
                    (plan_id, database_name, environment_name),
                )
                db_rows = cur.fetchall()
            rows = [
                {
                    "migration_ordinal": int(str(canonical_id).rsplit("-", 1)[1]),
                    "canonical_spatial_point_id": str(canonical_id),
                    "geometry_id": str(geometry_id),
                    "execution_id": str(execution_id),
                    "plan_version": int(plan_version),
                    "outcome": str(outcome),
                    "started_at": started_at,
                    "completed_at": completed_at,
                    "runtime_ms": int((completed_at - started_at).total_seconds() * 1000),
                    "logical_batch_id": _parse_detail(str(detail or "")).get("logical_batch_id"),
                }
                for canonical_id, geometry_id, execution_id, plan_version, outcome, started_at, completed_at, detail in db_rows
            ]
        if start_ordinal is not None:
            end = start_ordinal + count - 1 if count is not None else start_ordinal
            rows = [row for row in rows if start_ordinal <= row["migration_ordinal"] <= end]
        elif count is not None:
            rows = rows[:count]
        return tuple(rows)


__all__ = ["RecordAtomicPersistence"]
