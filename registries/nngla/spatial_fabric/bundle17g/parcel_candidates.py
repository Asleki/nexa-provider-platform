"""Bundle 17G parcel candidate formation from existing physical ground references."""
from __future__ import annotations
from hashlib import sha256

from .contracts import ParcelCandidateRecord, ParcelLifecycleStage


def candidate_identity(*, physical_ground_reference: str, source_reference: str) -> str:
    digest = sha256(f"{physical_ground_reference}\x1f{source_reference}".encode()).hexdigest()
    return f"parcelcand:nngla:{digest}"


def form_parcel_candidate(
    *, physical_ground_reference: str, proposed_land_use_code: str, source_reference: str,
    runtime_mode: str = "simulation", proposed_geometry_id: str = "", survey_status: str = "NOT_SURVEYED",
) -> ParcelCandidateRecord:
    return ParcelCandidateRecord(
        parcel_candidate_id=candidate_identity(physical_ground_reference=physical_ground_reference, source_reference=source_reference),
        physical_ground_reference=physical_ground_reference, proposed_land_use_code=proposed_land_use_code,
        proposed_geometry_id=proposed_geometry_id, survey_status=survey_status,
        lifecycle_stage=ParcelLifecycleStage.PARCEL_CANDIDATE, runtime_mode=runtime_mode,
        runtime_effect_scope="RUNTIME_SCOPED", source_reference=source_reference,
    )


__all__ = ["candidate_identity", "form_parcel_candidate"]
