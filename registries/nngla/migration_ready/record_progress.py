"""Deterministic NNGLA migration ordinals and PostgreSQL-derived progress."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Mapping, Sequence
from hashlib import sha256

from .contracts import ReconciliationAction, ReconciliationItem
from .record_contracts import (
    RecordMigrationProgress,
    RecordMigrationWindow,
    RecordReceiptObservation,
)


def canonical_migration_order(crosswalks: Mapping[str, object]) -> tuple[str, ...]:
    """Return candidates in immutable NG-SPT numeric order, never CSV/random order."""
    rows = sorted(
        crosswalks.values(),
        key=lambda row: int(str(getattr(row, "canonical_spatial_point_id")).rsplit("-", 1)[1]),
    )
    candidate_ids = tuple(str(getattr(row, "coordinate_candidate_id")) for row in rows)
    canonical_ids = tuple(str(getattr(row, "canonical_spatial_point_id")) for row in rows)
    expected = tuple(f"NG-SPT-{ordinal:06d}" for ordinal in range(1, len(rows) + 1))
    if canonical_ids != expected:
        raise ValueError("NNGLA canonical migration order must be contiguous NG-SPT-000001..N")
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("NNGLA coordinate candidate IDs must be unique")
    return candidate_ids


def ordinal_maps(candidate_ids: Sequence[str]) -> tuple[dict[str, int], dict[int, str]]:
    ids = tuple(candidate_ids)
    by_candidate = {candidate_id: ordinal for ordinal, candidate_id in enumerate(ids, start=1)}
    if len(by_candidate) != len(ids):
        raise ValueError("candidate IDs must be unique before ordinal mapping")
    return by_candidate, {ordinal: candidate_id for candidate_id, ordinal in by_candidate.items()}


def logical_batch_id(
    *,
    plan_id: str,
    plan_version: int,
    source_sha256: str,
    start_ordinal: int,
    end_ordinal: int,
) -> str:
    material = "|".join(
        (plan_id, str(plan_version), source_sha256, str(start_ordinal), str(end_ordinal))
    )
    return "nnglabatch:spatial:mr:" + sha256(material.encode("utf-8")).hexdigest()[:24]


def assess_record_progress(
    *,
    candidate_ids: Sequence[str],
    reconciliation: Sequence[ReconciliationItem],
    observations: Sequence[RecordReceiptObservation],
) -> RecordMigrationProgress:
    ids = tuple(candidate_ids)
    action_by_id = {item.coordinate_candidate_id: item.action for item in reconciliation}
    missing_actions = [candidate_id for candidate_id in ids if candidate_id not in action_by_id]
    if missing_actions:
        raise ValueError("reconciliation is missing governed candidates")

    canonical_count = sum(
        1 for candidate_id in ids if action_by_id[candidate_id] is ReconciliationAction.REUSE_CANONICAL
    )
    first_unfulfilled = next(
        (
            ordinal
            for ordinal, candidate_id in enumerate(ids, start=1)
            if action_by_id[candidate_id] is not ReconciliationAction.REUSE_CANONICAL
        ),
        None,
    )
    contiguous = len(ids) if first_unfulfilled is None else first_unfulfilled - 1

    by_batch: dict[str, list[RecordReceiptObservation]] = defaultdict(list)
    for observation in observations:
        by_batch[observation.logical_batch_id].append(observation)

    incomplete: list[tuple[str, int, int, int]] = []
    for batch_id, rows in by_batch.items():
        starts = {row.window_start_ordinal for row in rows}
        ends = {row.window_end_ordinal for row in rows}
        counts = {row.requested_count for row in rows}
        if len(starts) != 1 or len(ends) != 1 or len(counts) != 1:
            raise ValueError(f"logical batch receipt metadata drift: {batch_id}")
        start = next(iter(starts))
        end = next(iter(ends))
        requested = next(iter(counts))
        if requested != end - start + 1:
            raise ValueError(f"logical batch receipt count mismatch: {batch_id}")
        if not 1 <= start <= end <= len(ids):
            raise ValueError(f"logical batch receipt range outside source: {batch_id}")
        if any(
            action_by_id[ids[ordinal - 1]] is not ReconciliationAction.REUSE_CANONICAL
            for ordinal in range(start, end + 1)
        ):
            incomplete.append((batch_id, start, end, requested))

    if len(incomplete) > 1:
        raise ValueError("multiple incomplete NNGLA logical migration windows detected")

    active_id = active_start = active_end = active_requested = None
    if incomplete:
        active_id, active_start, active_end, active_requested = incomplete[0]
        if first_unfulfilled is None or not (active_start <= first_unfulfilled <= active_end):
            raise ValueError("incomplete logical batch does not contain the first unfulfilled ordinal")

    return RecordMigrationProgress(
        total_count=len(ids),
        canonical_count=canonical_count,
        contiguous_completed_ordinal=contiguous,
        first_unfulfilled_ordinal=first_unfulfilled,
        migration_complete=first_unfulfilled is None,
        active_logical_batch_id=active_id,
        active_window_start_ordinal=active_start,
        active_window_end_ordinal=active_end,
        active_requested_count=active_requested,
    )


def select_record_window(
    *,
    candidate_ids: Sequence[str],
    progress: RecordMigrationProgress,
    requested_count: int,
    plan_id: str,
    plan_version: int,
    source_sha256: str,
    start_ordinal: int | None = None,
) -> RecordMigrationWindow | None:
    ids = tuple(candidate_ids)
    if requested_count < 1 or requested_count > len(ids):
        raise ValueError(f"count must be between 1 and {len(ids)}")
    if start_ordinal is not None and not 1 <= start_ordinal <= len(ids):
        raise ValueError(f"start_ordinal must be between 1 and {len(ids)}")

    # A normal run always finishes a durable incomplete logical window before
    # opening a new one, regardless of what count was typed on the reconnect.
    if start_ordinal is None and progress.active_logical_batch_id is not None:
        assert progress.first_unfulfilled_ordinal is not None
        assert progress.active_window_start_ordinal is not None
        assert progress.active_window_end_ordinal is not None
        assert progress.active_requested_count is not None
        execution_start = progress.first_unfulfilled_ordinal
        execution_end = progress.active_window_end_ordinal
        return RecordMigrationWindow(
            logical_batch_id=progress.active_logical_batch_id,
            window_start_ordinal=progress.active_window_start_ordinal,
            window_end_ordinal=progress.active_window_end_ordinal,
            requested_count=progress.active_requested_count,
            execution_start_ordinal=execution_start,
            execution_end_ordinal=execution_end,
            candidate_ids=ids[execution_start - 1 : execution_end],
            resumed=True,
            explicit_range=False,
        )

    if start_ordinal is None:
        if progress.migration_complete:
            return None
        assert progress.first_unfulfilled_ordinal is not None
        start = progress.first_unfulfilled_ordinal
        end = min(len(ids), start + requested_count - 1)
        batch_id = logical_batch_id(
            plan_id=plan_id,
            plan_version=plan_version,
            source_sha256=source_sha256,
            start_ordinal=start,
            end_ordinal=end,
        )
        return RecordMigrationWindow(
            logical_batch_id=batch_id,
            window_start_ordinal=start,
            window_end_ordinal=end,
            requested_count=end - start + 1,
            execution_start_ordinal=start,
            execution_end_ordinal=end,
            candidate_ids=ids[start - 1 : end],
            resumed=False,
            explicit_range=False,
        )

    end = min(len(ids), start_ordinal + requested_count - 1)
    first_missing = progress.first_unfulfilled_ordinal

    if progress.active_logical_batch_id is not None and first_missing is not None:
        # Completed historical ranges may still be explicitly rechecked while an
        # incomplete window exists, but no new data may be inserted around it.
        if end >= first_missing:
            raise ValueError("an incomplete logical window exists; resume it before opening/inserting another range")
    elif first_missing is not None and start_ordinal > first_missing:
        raise ValueError(
            f"explicit range would skip unresolved ordinal {first_missing}; start at or before the first unfulfilled record"
        )

    batch_id = logical_batch_id(
        plan_id=plan_id,
        plan_version=plan_version,
        source_sha256=source_sha256,
        start_ordinal=start_ordinal,
        end_ordinal=end,
    )
    return RecordMigrationWindow(
        logical_batch_id=batch_id,
        window_start_ordinal=start_ordinal,
        window_end_ordinal=end,
        requested_count=end - start_ordinal + 1,
        execution_start_ordinal=start_ordinal,
        execution_end_ordinal=end,
        candidate_ids=ids[start_ordinal - 1 : end],
        resumed=False,
        explicit_range=True,
    )


__all__ = [
    "canonical_migration_order",
    "ordinal_maps",
    "logical_batch_id",
    "assess_record_progress",
    "select_record_window",
]
