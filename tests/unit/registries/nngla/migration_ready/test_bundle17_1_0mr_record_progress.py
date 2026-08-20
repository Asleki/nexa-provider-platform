import pytest

from registries.nngla.migration_ready.contracts import ReconciliationAction, ReconciliationItem
from registries.nngla.migration_ready.record_contracts import RecordReceiptObservation
from registries.nngla.migration_ready.record_progress import (
    assess_record_progress,
    canonical_migration_order,
    select_record_window,
)
from registries.nngla.spatial_fabric.bundle17e.canonical import canonical_by_candidate

PLAN_ID = "P006.7.11.7.0MR-SPATIAL-BATCH"
SOURCE = "a" * 64


def _items(ids, reused):
    return tuple(
        ReconciliationItem(
            candidate_id,
            f"NG-SPT-{ordinal:06d}",
            f"NG-GEO-{ordinal + 21:06d}",
            ReconciliationAction.REUSE_CANONICAL if ordinal <= reused else ReconciliationAction.INSERT_NEW,
            "EXACT_POSTGRESQL_STATE_MATCH" if ordinal <= reused else "TARGET_IDENTITIES_AVAILABLE",
        )
        for ordinal, candidate_id in enumerate(ids, start=1)
    )


def _observation(ids, ordinal, start=1, end=800):
    return RecordReceiptObservation(
        execution_id=f"nnglarun:spatial:mr:{ordinal:024d}",
        logical_batch_id="nnglabatch:spatial:mr:" + "b" * 24,
        window_start_ordinal=start,
        window_end_ordinal=end,
        requested_count=end - start + 1,
        migration_ordinal=ordinal,
        coordinate_candidate_id=ids[ordinal - 1],
        canonical_spatial_point_id=f"NG-SPT-{ordinal:06d}",
        geometry_id=f"NG-GEO-{ordinal + 21:06d}",
        outcome="INSERTED",
        completed_at="2026-08-20T00:00:00+00:00",
    )


def test_canonical_order_is_ng_spt_sequence_not_physical_csv_order():
    crosswalks = canonical_by_candidate()
    ids = canonical_migration_order(crosswalks)
    assert len(ids) == 2411
    assert crosswalks[ids[0]].canonical_spatial_point_id == "NG-SPT-000001"
    assert crosswalks[ids[499]].canonical_spatial_point_id == "NG-SPT-000500"
    assert crosswalks[ids[-1]].canonical_spatial_point_id == "NG-SPT-002411"


def test_normal_next_window_starts_at_first_unfulfilled_ordinal():
    ids = canonical_migration_order(canonical_by_candidate())
    progress = assess_record_progress(candidate_ids=ids, reconciliation=_items(ids, 500), observations=())
    window = select_record_window(
        candidate_ids=ids,
        progress=progress,
        requested_count=500,
        plan_id=PLAN_ID,
        plan_version=3,
        source_sha256=SOURCE,
    )
    assert progress.contiguous_completed_ordinal == 500
    assert progress.first_unfulfilled_ordinal == 501
    assert (window.window_start_ordinal, window.window_end_ordinal) == (501, 1000)
    assert (window.execution_start_ordinal, window.execution_end_ordinal) == (501, 1000)


def test_incomplete_800_window_resumes_at_601_and_keeps_original_end():
    ids = canonical_migration_order(canonical_by_candidate())
    observations = tuple(_observation(ids, ordinal) for ordinal in range(1, 601))
    progress = assess_record_progress(candidate_ids=ids, reconciliation=_items(ids, 600), observations=observations)
    window = select_record_window(
        candidate_ids=ids,
        progress=progress,
        requested_count=500,  # reconnect may type another count; durable window still wins
        plan_id=PLAN_ID,
        plan_version=3,
        source_sha256=SOURCE,
    )
    assert progress.active_window_start_ordinal == 1
    assert progress.active_window_end_ordinal == 800
    assert progress.first_unfulfilled_ordinal == 601
    assert window.resumed is True
    assert window.requested_count == 800
    assert (window.execution_start_ordinal, window.execution_end_ordinal) == (601, 800)
    assert window.selected_count == 200


def test_explicit_completed_range_is_allowed_but_skipping_first_missing_is_not():
    ids = canonical_migration_order(canonical_by_candidate())
    progress = assess_record_progress(candidate_ids=ids, reconciliation=_items(ids, 500), observations=())
    verification = select_record_window(
        candidate_ids=ids,
        progress=progress,
        requested_count=500,
        start_ordinal=1,
        plan_id=PLAN_ID,
        plan_version=3,
        source_sha256=SOURCE,
    )
    assert verification.explicit_range is True
    assert (verification.execution_start_ordinal, verification.execution_end_ordinal) == (1, 500)
    with pytest.raises(ValueError, match="skip unresolved ordinal 501"):
        select_record_window(
            candidate_ids=ids,
            progress=progress,
            requested_count=100,
            start_ordinal=1001,
            plan_id=PLAN_ID,
            plan_version=3,
            source_sha256=SOURCE,
        )
