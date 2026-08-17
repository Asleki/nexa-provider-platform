"""Bundle 17G physical-ground, parcel-candidate and reservation contracts."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import re

_PARCEL_RE = re.compile(r"^NV-(\d{2})-(\d{3})-(\d{4,})$")
_GEO_RE = re.compile(r"^NG-GEO-\d{6}$")


class ParcelLifecycleStage(str, Enum):
    PHYSICAL_GROUND = "PHYSICAL_GROUND"
    PARCEL_CANDIDATE = "PARCEL_CANDIDATE"
    REFERENCE_RESERVED = "REFERENCE_RESERVED"
    SURVEYED = "SURVEYED"
    QUALIFIED = "QUALIFIED"
    RECOGNIZED = "RECOGNIZED"
    REGISTERED = "REGISTERED"


@dataclass(frozen=True, slots=True)
class CadastralSeriesPolicy:
    definition_id: str
    parcel_id_pattern: str
    cadastral_zone_semantics: str
    cadastral_series_semantics: str
    sequence_semantics: str
    minimum_sequence_width: int
    allocation_authority_code: str
    sovereign_reservation_runtime: str
    administrative_area_dependency: str
    status: str

    def __post_init__(self) -> None:
        if self.definition_id != "cadseries-policy:nngla:default":
            raise ValueError("Bundle 17G has one governed cadastral-series policy contract")
        if self.parcel_id_pattern != r"^NV-\d{2}-\d{3}-\d{4,}$":
            raise ValueError("parcel identity pattern must reuse locked NV contract")
        if self.minimum_sequence_width != 4 or self.allocation_authority_code != "NNGLA":
            raise ValueError("invalid cadastral allocation authority contract")
        if self.administrative_area_dependency != "INDEPENDENT_OF_ADMINISTRATIVE_BOUNDARIES":
            raise ValueError("cadastral zones must not encode mutable administrative areas")
        if self.status != "ACTIVE":
            raise ValueError("cadastral-series policy must be active")


@dataclass(frozen=True, slots=True)
class CadastralSeriesDefinition:
    zone_code: str
    series_code: str
    authority_code: str = "NNGLA"
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        if re.fullmatch(r"\d{2}", self.zone_code) is None:
            raise ValueError("cadastral zone must be exactly two digits")
        if re.fullmatch(r"\d{3}", self.series_code) is None:
            raise ValueError("cadastral series must be exactly three digits")
        if self.authority_code != "NNGLA" or self.status != "ACTIVE":
            raise ValueError("only active NNGLA cadastral series can allocate parcel references")

    @property
    def parcel_prefix(self) -> str:
        return f"NV-{self.zone_code}-{self.series_code}"


@dataclass(frozen=True, slots=True)
class ParcelCandidateRecord:
    parcel_candidate_id: str
    physical_ground_reference: str
    proposed_land_use_code: str
    proposed_geometry_id: str
    survey_status: str
    lifecycle_stage: ParcelLifecycleStage
    runtime_mode: str
    runtime_effect_scope: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.parcel_candidate_id.startswith("parcelcand:nngla:"):
            raise ValueError("parcel candidate uses private parcelcand:nngla: identity, not sovereign parcel namespace")
        if _PARCEL_RE.fullmatch(self.parcel_candidate_id):
            raise ValueError("parcel candidate must not already be a sovereign parcel identity")
        if not (self.physical_ground_reference.startswith("NG-SPT-") or self.physical_ground_reference.startswith("NG-GEO-") or self.physical_ground_reference.startswith("ground:nngla:")):
            raise ValueError("physical ground reference must reference governed spatial ground, not a parcel")
        if self.proposed_geometry_id and _GEO_RE.fullmatch(self.proposed_geometry_id) is None:
            raise ValueError("proposed parcel geometry must use governed geometry identity")
        if self.lifecycle_stage not in {ParcelLifecycleStage.PARCEL_CANDIDATE, ParcelLifecycleStage.SURVEYED, ParcelLifecycleStage.QUALIFIED, ParcelLifecycleStage.RECOGNIZED}:
            raise ValueError("candidate record cannot masquerade as physical ground, reservation or registered parcel")
        if self.runtime_mode not in {"simulation", "production"}:
            raise ValueError("parcel candidate runtime must be simulation or production")
        if self.runtime_effect_scope != "RUNTIME_SCOPED":
            raise ValueError("parcel candidate operation remains runtime scoped")
        if not self.source_reference:
            raise ValueError("parcel candidate source reference required")


@dataclass(frozen=True, slots=True)
class ParcelReferenceReservation:
    reservation_id: str
    parcel_candidate_id: str
    parcel_id: str
    cadastral_zone: str
    cadastral_series: str
    parcel_sequence: str
    reservation_status: str
    legal_effect: bool
    canonical_parcel_registered: bool
    authority_runtime_mode: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.reservation_id.startswith("parcelres:nngla:"):
            raise ValueError("invalid parcel reference reservation identity")
        match = _PARCEL_RE.fullmatch(self.parcel_id)
        if match is None:
            raise ValueError("reserved parcel reference must use locked NV-##-###-####+ format")
        if (self.cadastral_zone, self.cadastral_series, self.parcel_sequence) != match.groups():
            raise ValueError("parcel reservation components must match parcel_id")
        if self.reservation_status != "RESERVED":
            raise ValueError("Bundle 17G reservation record is a reservation, not issuance/registration")
        if self.legal_effect or self.canonical_parcel_registered:
            raise ValueError("parcel reference reservation must not claim legal/registered parcel existence")
        if self.authority_runtime_mode != "production":
            raise ValueError("sovereign parcel reference reservation is production-authority operation")


@dataclass(frozen=True, slots=True)
class ParcelGeometryCandidate:
    parcel_geometry_candidate_id: str
    parcel_candidate_id: str
    geometry_id: str
    geometry_type_code: str
    crs_code: str
    ring_closed: bool
    geometry_valid: bool
    sovereign_land_relation: str
    overlap_status: str
    survey_id: str
    geometry_status: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.parcel_geometry_candidate_id.startswith("parcelgeo:nngla:"):
            raise ValueError("invalid parcel geometry candidate identity")
        if _GEO_RE.fullmatch(self.geometry_id) is None:
            raise ValueError("parcel geometry candidate must reference governed geometry identity")
        if self.geometry_type_code not in {"POLYGON", "MULTIPOLYGON"}:
            raise ValueError("cadastral parcels require polygonal geometry")
        if self.crs_code != "NG-CRS-EPSG4326":
            raise ValueError("cadastral geometry must use governed CRS")
        if self.survey_id and re.fullmatch(r"NG-SRV-\d{6}", self.survey_id) is None:
            raise ValueError("survey identity invalid")


@dataclass(frozen=True, slots=True)
class ParcelLineageCandidate:
    lineage_candidate_id: str
    action: str
    predecessor_parcel_ids: tuple[str, ...]
    successor_parcel_ids: tuple[str, ...]
    effective_on: str
    source_reference: str

    def __post_init__(self) -> None:
        if not self.lineage_candidate_id.startswith("parcel-lineage-candidate:"):
            raise ValueError("invalid parcel lineage candidate identity")
        if self.action not in {"SUBDIVISION", "CONSOLIDATION"}:
            raise ValueError("unsupported parcel lineage action")
        ids = self.predecessor_parcel_ids + self.successor_parcel_ids
        if not ids or any(_PARCEL_RE.fullmatch(value) is None for value in ids):
            raise ValueError("lineage candidates reference governed parcel identities")
        if len(set(ids)) != len(ids):
            raise ValueError("parcel lineage candidate identities may not repeat")


@dataclass(frozen=True, slots=True)
class ParcelQualificationResult:
    parcel_candidate_id: str
    parcel_id: str
    physical_ground_distinct: bool
    reference_reserved: bool
    geometry_valid: bool
    survey_valid: bool
    land_use_valid: bool
    sovereign_land_valid: bool
    overlap_clear_or_deferred: bool
    recognition_ready: bool
    qualification_status: str
    findings: str


__all__ = [
    "ParcelLifecycleStage", "CadastralSeriesPolicy", "CadastralSeriesDefinition", "ParcelCandidateRecord",
    "ParcelReferenceReservation", "ParcelGeometryCandidate", "ParcelLineageCandidate", "ParcelQualificationResult",
]
