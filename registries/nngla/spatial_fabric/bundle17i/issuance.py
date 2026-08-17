"""Bundle 17I title issuance candidate qualification and final title adapter."""
from __future__ import annotations

from datetime import date

from registries.nngla.titles import TitleRecord, TitleStatus
from ._shared import TITLE_TYPES_PATH, TENURE_TYPES_PATH, csv_rows, stable_id
from .contracts import TitleIssuanceCandidate, TitleQualificationResult, TitleReferenceReservation


def form_title_issuance_candidate(
    reservation: TitleReferenceReservation, *, parcel_id: str, title_type_code: str, tenure_type_code: str,
    holder_reference: str, prior_title_id: str = "", source_reference: str,
) -> TitleIssuanceCandidate:
    identity = stable_id("titleissuecand:nngla:", reservation.reservation_id, parcel_id, title_type_code, tenure_type_code, holder_reference, prior_title_id)
    return TitleIssuanceCandidate(
        issuance_candidate_id=identity, reservation_id=reservation.reservation_id, title_id=reservation.reserved_title_id,
        parcel_id=parcel_id, title_type_code=title_type_code, tenure_type_code=tenure_type_code,
        holder_reference=holder_reference, issuance_status="ISSUANCE_CANDIDATE", prior_title_id=prior_title_id,
        runtime_mode="production", source_reference=source_reference,
    )


def qualify_title_issuance(reservation: TitleReferenceReservation, candidate: TitleIssuanceCandidate) -> TitleQualificationResult:
    title_types = {row["title_type_code"]: row for row in csv_rows(TITLE_TYPES_PATH)}
    tenure_types = {row["tenure_type_code"] for row in csv_rows(TENURE_TYPES_PATH)}
    reservation_ok = (
        reservation.reservation_id == candidate.reservation_id
        and reservation.reserved_title_id == candidate.title_id
        and not reservation.legal_title_exists
    )
    parcel_ok = bool(candidate.parcel_id)
    title_type = title_types.get(candidate.title_type_code)
    title_type_ok = title_type is not None and title_type["status"] == "ACTIVE" and title_type["registrable"].lower() == "true"
    tenure_ok = candidate.tenure_type_code in tenure_types and bool(title_type) and title_type["tenure_type_code"] == candidate.tenure_type_code
    holder_ok = bool(candidate.holder_reference and not any(ch.isspace() for ch in candidate.holder_reference))
    lineage_ok = not candidate.prior_title_id or candidate.prior_title_id != candidate.title_id
    ready = all((reservation_ok, parcel_ok, title_type_ok, tenure_ok, holder_ok, lineage_ok))
    findings = []
    if not reservation_ok: findings.append("TITLE_REFERENCE_RESERVATION_INVALID")
    if not parcel_ok: findings.append("PARCEL_LINK_REQUIRED_FOR_ISSUANCE")
    if not title_type_ok: findings.append("TITLE_TYPE_INVALID")
    if not tenure_ok: findings.append("TENURE_TYPE_INVALID_OR_MISMATCH")
    if not holder_ok: findings.append("HOLDER_REFERENCE_INVALID")
    if not lineage_ok: findings.append("REPLACEMENT_LINEAGE_SELF_REFERENCE")
    return TitleQualificationResult(
        title_id=candidate.title_id, reservation_valid=reservation_ok, parcel_valid=parcel_ok,
        title_type_valid=title_type_ok, tenure_valid=tenure_ok, holder_reference_valid=holder_ok,
        replacement_lineage_valid=lineage_ok, issuance_ready=ready,
        qualification_status="PASS" if ready else "FAIL", findings=";".join(findings),
    )


def issue_qualified_title(
    reservation: TitleReferenceReservation, candidate: TitleIssuanceCandidate, *, effective_on: date, source_reference: str,
) -> TitleRecord:
    result = qualify_title_issuance(reservation, candidate)
    if not result.issuance_ready:
        raise ValueError(f"title issuance candidate is not qualified: {result.findings}")
    return TitleRecord(
        title_id=candidate.title_id, parcel_id=candidate.parcel_id, title_type_code=candidate.title_type_code,
        tenure_type_code=candidate.tenure_type_code, holder_reference=candidate.holder_reference,
        title_status=TitleStatus.ISSUED, effective_from=effective_on, effective_to=None,
        source_reference=source_reference,
    )


__all__ = ["form_title_issuance_candidate", "qualify_title_issuance", "issue_qualified_title"]
