"""Bundle 17I legal reference reservation, title issuance and state-land candidate contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

_TITLE_RE = re.compile(r"^NG-TTL-\d{6}$")
_PARCEL_RE = re.compile(r"^NV-\d{2}-\d{3}-\d{4,}$")


class TitleLifecycleStage(str, Enum):
    TITLE_NUMBER_RESERVED = "TITLE_NUMBER_RESERVED"
    ISSUANCE_CANDIDATE = "ISSUANCE_CANDIDATE"
    TITLE_ISSUED = "TITLE_ISSUED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"
    REPLACED = "REPLACED"
    HISTORICAL = "HISTORICAL"


@dataclass(frozen=True, slots=True)
class TitleNumberSeriesDefinition:
    series_id: str
    title_id_pattern: str
    allocation_scope: str
    prefix: str
    sequence_width: int
    minimum_sequence: int
    sequence_semantics: str
    issuing_authority_code: str
    reservation_runtime: str
    status: str

    def __post_init__(self) -> None:
        if self.series_id != "titleseries:nngla:sovereign":
            raise ValueError("Bundle 17I uses one sovereign title-number series")
        if self.title_id_pattern != r"^NG-TTL-\d{6}$" or self.prefix != "NG-TTL-" or self.sequence_width != 6:
            raise ValueError("title series must reuse locked NG-TTL-###### contract")
        if self.allocation_scope != "SOVEREIGN_GLOBAL" or self.sequence_semantics != "MONOTONIC_NO_REUSE":
            raise ValueError("title numbering must be sovereign-global monotonic no-reuse")
        if self.minimum_sequence < 1 or self.issuing_authority_code != "NNGLA":
            raise ValueError("title series allocation authority invalid")
        if self.reservation_runtime != "PRODUCTION_AUTHORITY" or self.status != "ACTIVE":
            raise ValueError("title number reservation requires active production authority")


@dataclass(frozen=True, slots=True)
class TitleReferenceReservation:
    reservation_id: str
    series_id: str
    reserved_title_id: str
    parcel_id: str
    holder_reference: str
    idempotency_key: str
    reservation_status: str
    legal_title_exists: bool
    authority_runtime_mode: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.reservation_id.startswith("titleres:nngla:"):
            raise ValueError("title reservation identity invalid")
        if self.series_id != "titleseries:nngla:sovereign":
            raise ValueError("unknown title number series")
        if _TITLE_RE.fullmatch(self.reserved_title_id) is None:
            raise ValueError("reserved title reference must use locked NG-TTL identity")
        if self.parcel_id and _PARCEL_RE.fullmatch(self.parcel_id) is None:
            raise ValueError("optional parcel link must use governed parcel identity")
        if self.holder_reference and any(ch.isspace() for ch in self.holder_reference):
            raise ValueError("holder reference must remain opaque")
        if not self.idempotency_key:
            raise ValueError("title reference reservation requires idempotency key")
        if self.reservation_status != "TITLE_NUMBER_RESERVED" or self.legal_title_exists:
            raise ValueError("title reference reservation must not claim title issuance")
        if self.authority_runtime_mode != "production":
            raise ValueError("sovereign title reference reservation is production-authority operation")


@dataclass(frozen=True, slots=True)
class TitleIssuanceCandidate:
    issuance_candidate_id: str
    reservation_id: str
    title_id: str
    parcel_id: str
    title_type_code: str
    tenure_type_code: str
    holder_reference: str
    issuance_status: str
    prior_title_id: str
    runtime_mode: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.issuance_candidate_id.startswith("titleissuecand:nngla:"):
            raise ValueError("title issuance candidate identity invalid")
        if not self.reservation_id.startswith("titleres:nngla:"):
            raise ValueError("title issuance must reference a reservation")
        if _TITLE_RE.fullmatch(self.title_id) is None:
            raise ValueError("title issuance identity invalid")
        if _PARCEL_RE.fullmatch(self.parcel_id) is None:
            raise ValueError("title issuance requires governed parcel identity")
        if not self.title_type_code or not self.tenure_type_code or not self.holder_reference:
            raise ValueError("title issuance requires type, tenure and holder reference")
        if any(ch.isspace() for ch in self.holder_reference):
            raise ValueError("holder reference must remain opaque")
        if self.prior_title_id and _TITLE_RE.fullmatch(self.prior_title_id) is None:
            raise ValueError("prior title identity invalid")
        if self.issuance_status != "ISSUANCE_CANDIDATE" or self.runtime_mode != "production":
            raise ValueError("title issuance candidate must remain production-authority pre-issuance")


@dataclass(frozen=True, slots=True)
class StateLandCandidateRecord:
    state_land_candidate_id: str
    parcel_id: str
    state_land_category_code: str
    administrative_area_id: str
    candidate_status: str
    legal_state_land_exists: bool
    runtime_mode: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.state_land_candidate_id.startswith("statelandcand:nngla:"):
            raise ValueError("state-land candidate identity invalid")
        if _PARCEL_RE.fullmatch(self.parcel_id) is None:
            raise ValueError("state-land legal-link candidate requires governed parcel")
        if not self.state_land_category_code:
            raise ValueError("state-land category required")
        if self.candidate_status != "CANDIDATE" or self.legal_state_land_exists:
            raise ValueError("state-land candidate must not claim legal state-land establishment")
        if self.runtime_mode not in {"simulation", "production"}:
            raise ValueError("state-land candidate runtime invalid")


@dataclass(frozen=True, slots=True)
class TitleQualificationResult:
    title_id: str
    reservation_valid: bool
    parcel_valid: bool
    title_type_valid: bool
    tenure_valid: bool
    holder_reference_valid: bool
    replacement_lineage_valid: bool
    issuance_ready: bool
    qualification_status: str
    findings: str


__all__ = [
    "TitleLifecycleStage", "TitleNumberSeriesDefinition", "TitleReferenceReservation", "TitleIssuanceCandidate",
    "StateLandCandidateRecord", "TitleQualificationResult",
]
