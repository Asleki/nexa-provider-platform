"""Deterministic configurable batching for Bundle 17.0MR."""
from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from .contracts import BatchProfile, BatchWindow, ReconciliationAction, ReconciliationItem


def _numeric_suffix(value: str) -> int:
    try:
        return int(str(value).rsplit("-", 1)[1])
    except (IndexError, ValueError) as exc:
        raise ValueError(f"identifier has no numeric suffix: {value}") from exc


def ordered_candidate_ids(crosswalks: Mapping[str, object]) -> tuple[str, ...]:
    """Order candidates by their locked canonical NG-SPT sequence."""
    rows = list(crosswalks.values())
    rows.sort(key=lambda row: _numeric_suffix(getattr(row, "canonical_spatial_point_id")))
    candidate_ids = tuple(getattr(row, "coordinate_candidate_id") for row in rows)
    if len(candidate_ids) != len(set(candidate_ids)):
        raise ValueError("candidate IDs must be unique before batching")
    return candidate_ids


def build_profile_windows(candidate_ids: Sequence[str], profile: BatchProfile) -> tuple[BatchWindow, ...]:
    ids = tuple(candidate_ids)
    if len(ids) != profile.expected_total:
        raise ValueError(
            f"profile {profile.profile_id} expects {profile.expected_total} records, got {len(ids)}"
        )
    windows: list[BatchWindow] = []
    offset = 0
    for batch_number, size in enumerate(profile.batch_sizes, start=1):
        selected = ids[offset : offset + size]
        windows.append(BatchWindow(batch_number, offset, offset + len(selected), selected))
        offset += size
    if offset != len(ids):
        raise ValueError("batch profile did not consume the full candidate set")
    return tuple(windows)


def build_fixed_windows(candidate_ids: Sequence[str], batch_size: int) -> tuple[BatchWindow, ...]:
    if batch_size < 1 or batch_size > 10_000:
        raise ValueError("batch_size must be between 1 and 10000")
    ids = tuple(candidate_ids)
    windows: list[BatchWindow] = []
    offset = 0
    number = 1
    while offset < len(ids):
        selected = ids[offset : offset + batch_size]
        windows.append(BatchWindow(number, offset, offset + len(selected), selected))
        offset += len(selected)
        number += 1
    return tuple(windows)


def windows_requiring_write(
    windows: Iterable[BatchWindow], reconciliation: Iterable[ReconciliationItem]
) -> tuple[BatchWindow, ...]:
    action_by_id = {item.coordinate_candidate_id: item.action for item in reconciliation}
    out: list[BatchWindow] = []
    for window in windows:
        if any(action_by_id[candidate_id] is ReconciliationAction.INSERT_NEW for candidate_id in window.candidate_ids):
            out.append(window)
    return tuple(out)


__all__ = [
    "ordered_candidate_ids",
    "build_profile_windows",
    "build_fixed_windows",
    "windows_requiring_write",
]
