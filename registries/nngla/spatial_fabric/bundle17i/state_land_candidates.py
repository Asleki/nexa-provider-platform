"""Bundle 17I state-land candidate formation without fabricating legal state ownership."""
from __future__ import annotations

from datetime import date
from registries.nngla.state_land import StateLandRecord
from ._shared import STATE_LAND_CATEGORIES_PATH, csv_rows, stable_id
from .contracts import StateLandCandidateRecord


def form_state_land_candidate(
    *, parcel_id: str, state_land_category_code: str, administrative_area_id: str = "",
    runtime_mode: str = "simulation", source_reference: str,
) -> StateLandCandidateRecord:
    known = {row["state_land_category_code"] for row in csv_rows(STATE_LAND_CATEGORIES_PATH)}
    if state_land_category_code not in known:
        raise ValueError("unknown governed state-land category")
    identity = stable_id("statelandcand:nngla:", parcel_id, state_land_category_code, administrative_area_id, runtime_mode, source_reference)
    return StateLandCandidateRecord(
        state_land_candidate_id=identity, parcel_id=parcel_id, state_land_category_code=state_land_category_code,
        administrative_area_id=administrative_area_id, candidate_status="CANDIDATE", legal_state_land_exists=False,
        runtime_mode=runtime_mode, source_reference=source_reference,
    )


def recognize_state_land_candidate(candidate: StateLandCandidateRecord, *, effective_on: date, source_reference: str) -> StateLandRecord:
    if candidate.runtime_mode != "production":
        raise ValueError("state-land legal establishment requires production authority")
    record_id = stable_id("stateland:nngla:", candidate.parcel_id, candidate.state_land_category_code, str(effective_on))
    return StateLandRecord(
        state_land_record_id=record_id, parcel_id=candidate.parcel_id,
        state_land_category_code=candidate.state_land_category_code,
        administrative_area_id=candidate.administrative_area_id or None, status="ACTIVE",
        effective_from=effective_on, effective_to=None, source_reference=source_reference,
    )


__all__ = ["form_state_land_candidate", "recognize_state_land_candidate"]
