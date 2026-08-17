"""Bundle 17I legal-foundation qualification preserving empty Day-Zero title/state-land registers."""
from __future__ import annotations

from datetime import date

from ._shared import (
    DAY_ZERO_TITLE_PATH, DAY_ZERO_STATE_LAND_PATH, TITLE_TYPES_PATH, TENURE_TYPES_PATH,
    STATE_LAND_CATEGORIES_PATH, csv_rows,
)
from .artifacts import artifact_drift_findings, artifact_paths
from .issuance import form_title_issuance_candidate, issue_qualified_title, qualify_title_issuance
from .postgresql_contract import load_schema17i_sql, qualify_schema17i_sql
from .state_land_candidates import form_state_land_candidate, recognize_state_land_candidate
from .title_allocator import MemoryTitleReferenceAllocator
from .title_series import load_title_series


def bundle17i_findings() -> tuple[str, ...]:
    findings: list[str] = []
    if csv_rows(DAY_ZERO_TITLE_PATH): findings.append("DAY_ZERO_TITLE_REGISTER_MUST_REMAIN_EMPTY")
    if csv_rows(DAY_ZERO_STATE_LAND_PATH): findings.append("DAY_ZERO_STATE_LAND_REGISTER_MUST_REMAIN_EMPTY")
    if len(csv_rows(TITLE_TYPES_PATH)) != 6: findings.append("TITLE_TYPE_VOCABULARY_DRIFT")
    if len(csv_rows(TENURE_TYPES_PATH)) != 7: findings.append("TENURE_TYPE_VOCABULARY_DRIFT")
    if len(csv_rows(STATE_LAND_CATEGORIES_PATH)) != 6: findings.append("STATE_LAND_CATEGORY_VOCABULARY_DRIFT")
    findings.extend(artifact_drift_findings())
    findings.extend(qualify_schema17i_sql(load_schema17i_sql()))
    for key in ("title_reservations","title_issuance_candidates","state_land_candidates","title_bootstrap_v002","state_land_bootstrap_v002"):
        if csv_rows(artifact_paths()[key]): findings.append(f"FABRICATED_DAY_ZERO_ROWS:{key}")
    try:
        series = load_title_series()
        allocator = MemoryTitleReferenceAllocator(start_sequence=1)
        reservation = allocator.reserve(series, idempotency_key="qualification:title:1")
        if reservation.parcel_id or reservation.holder_reference or reservation.legal_title_exists:
            findings.append("TITLE_REFERENCE_RESERVATION_FALSE_LEGAL_EFFECT")
        candidate = form_title_issuance_candidate(
            reservation, parcel_id="NV-01-001-0001", title_type_code="FREEHOLD_TITLE", tenure_type_code="FREEHOLD",
            holder_reference="citizen:qualification:1", source_reference="qualification:title-issuance",
        )
        result = qualify_title_issuance(reservation, candidate)
        if not result.issuance_ready: findings.append("TITLE_ISSUANCE_QUALIFICATION_FAILED")
        issued = issue_qualified_title(reservation, candidate, effective_on=date(2026,8,17), source_reference="qualification:title-issued")
        if issued.title_id != reservation.reserved_title_id: findings.append("TITLE_ISSUANCE_CHANGED_RESERVED_IDENTITY")
        state_candidate = form_state_land_candidate(
            parcel_id="NV-01-001-0002", state_land_category_code="GENERAL_STATE_LAND", runtime_mode="production",
            source_reference="qualification:state-land",
        )
        if state_candidate.legal_state_land_exists: findings.append("STATE_LAND_CANDIDATE_FALSE_LEGAL_EFFECT")
        recognized = recognize_state_land_candidate(state_candidate, effective_on=date(2026,8,17), source_reference="qualification:state-land-recognized")
        if recognized.parcel_id != state_candidate.parcel_id: findings.append("STATE_LAND_RECOGNITION_LINK_DRIFT")
    except Exception as exc:
        findings.append(f"LEGAL_FOUNDATION_OPERATIONAL_PROOF_FAILED:{exc}")
    return tuple(findings)


def bundle17i_is_qualified() -> bool:
    return not bundle17i_findings()


__all__ = ["bundle17i_findings", "bundle17i_is_qualified"]
