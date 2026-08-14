"""P006.7.5 geodetic, geometry-vocabulary, and survey-accuracy contracts.

These are governed reference definitions. Numeric survey tolerances remain
policy-deferred exactly as supplied by the validated NNGLA authority source.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date

@dataclass(frozen=True, slots=True)
class CoordinateReferenceSystemDefinition:
    crs_code: str
    authority_name: str
    authority_code: str
    canonical_name: str
    axis_order: str
    horizontal_unit: str
    vertical_unit: str
    is_geographic: bool
    is_default_novegeo: bool
    status: str
    effective_from: date
    effective_to: date | None
    notes: str
    def __post_init__(self) -> None:
        if not self.crs_code.startswith("NG-CRS-"):
            raise ValueError("crs_code must use governed NG-CRS identity")
        if not self.authority_name or not self.authority_code:
            raise ValueError("CRS authority and authority code are required")
        if self.axis_order != "LONGITUDE_LATITUDE":
            raise ValueError("NoveGeo application coordinate order must remain LONGITUDE_LATITUDE")
        if self.effective_to is not None and self.effective_to < self.effective_from:
            raise ValueError("CRS effective_to cannot precede effective_from")

@dataclass(frozen=True, slots=True)
class GeometryTypeDefinition:
    geometry_type_code: str
    canonical_label: str
    ogc_geometry_type: str
    dimension: int
    supports_multiple_parts: bool
    supports_ring: bool
    supports_linear_reference: bool
    description: str
    status: str
    def __post_init__(self) -> None:
        if self.geometry_type_code not in {"POINT","MULTIPOINT","LINESTRING","MULTILINESTRING","POLYGON","MULTIPOLYGON"}:
            raise ValueError("unsupported governed geometry type")
        if self.dimension != 2:
            raise ValueError("Bundle 15B source geometry vocabulary is two-dimensional")

@dataclass(frozen=True, slots=True)
class SurveyAccuracyClass:
    accuracy_class_code: str
    canonical_label: str
    usage_scope: str
    horizontal_accuracy_rule: str
    vertical_accuracy_rule: str
    legal_boundary_eligible: bool
    control_point_eligible: bool
    informational_only: bool
    requires_instrument_record: bool
    requires_surveyor_approval: bool
    status: str
    notes: str
    def __post_init__(self) -> None:
        if not self.accuracy_class_code or not self.canonical_label:
            raise ValueError("survey accuracy identity and label are required")
        if self.informational_only and self.legal_boundary_eligible:
            raise ValueError("informational-only accuracy cannot authorize a legal boundary")
        if self.status != "ACTIVE":
            raise ValueError("Bundle 15B only accepts active governed survey accuracy classes")

__all__=["CoordinateReferenceSystemDefinition","GeometryTypeDefinition","SurveyAccuracyClass"]
