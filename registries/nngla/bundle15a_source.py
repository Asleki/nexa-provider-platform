"""Read-only P006.7.3/P006.7.4 governed source snapshot loader."""
from __future__ import annotations
import csv
from datetime import date
from pathlib import Path
from registries.country.operating_context import RecordEffectScope
from .lifecycle import SpatialLifecycleStatus
from .geographic_features import FeatureTypeDefinition, GeographicOriginClass, GeographicFeatureRecognition
from .geographic_names import GeographicName, NamingStatusDefinition, GazetteActionDefinition, GeographicNameRole
from .name_assignments import GeographicNameAssignment
from .places import PlaceReference
from .administrative_areas import AdministrativeArea

DEFAULT_SOURCE_ROOT = Path(__file__).resolve().parents[2] / "data" / "novegeo" / "nngla" / "geographic-identity-places" / "source"

def _rows(relative: str, root: Path = DEFAULT_SOURCE_ROOT):
    with (root / relative).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))

def _bool(v: str) -> bool:
    if v.lower() not in {"true", "false"}: raise ValueError(f"invalid boolean {v!r}")
    return v.lower() == "true"

def _date(v: str): return date.fromisoformat(v) if v else None

def load_feature_types(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(FeatureTypeDefinition(r["feature_type_code"], r["feature_family_code"], r["canonical_label"], r["geometry_expectation"], GeographicOriginClass(r["origin_class"]), _bool(r["nngla_recognizable"]), _bool(r["nngla_creatable"]), _bool(r["nameable"]), _bool(r["supports_history"]), r["status"]) for r in _rows("02_controlled_codes/feature_type_codes.csv", root))

def load_naming_statuses(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(NamingStatusDefinition(r["naming_status_code"], r["canonical_label"], _bool(r["can_display_publicly"]), _bool(r["can_be_primary_name"]), _bool(r["requires_approval"]), _bool(r["requires_gazette"]), _bool(r["terminal_status"]), r["description"]) for r in _rows("02_controlled_codes/naming_status_codes.csv", root))

def load_gazette_actions(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(GazetteActionDefinition(r["gazette_action_code"], r["canonical_label"], r["subject_family"], _bool(r["creates_legal_effect"]), _bool(r["requires_previous_record"]), _bool(r["reversible"]), r["status"], r["description"]) for r in _rows("02_controlled_codes/gazette_action_types.csv", root))

def load_feature_recognitions(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(GeographicFeatureRecognition(r["feature_candidate_id"], r["source_feature_id"], r["feature_type_code"], r["source_dataset_id"], r["source_dataset_version"], GeographicOriginClass(r["physical_origin_class"]), SpatialLifecycleStatus(r["lifecycle_status_code"]), r["recognition_status"], r["source_geometry_reference"] or None, r["crs_code"] or None, RecordEffectScope(r["runtime_effect_scope"]), r["source_authority"], r["source_basis"], r["candidate_status"]) for r in _rows("05_geographic_candidates/geographic_feature_candidates.csv", root))

def load_settlement_names(root: Path = DEFAULT_SOURCE_ROOT):
    out=[]
    for r in _rows("04_name_catalogues/settlement_name_catalogue.csv", root):
        out.append(GeographicName(r["settlement_name_record_id"], r["canonical_name"], r["ascii_name"], "SETTLEMENT", r["naming_status_code"], RecordEffectScope(r["runtime_effect_scope"]), r["source_dataset_id"], r["source_basis"], r["record_status"], r["nickname"] or None))
    return tuple(out)

def load_places(root: Path = DEFAULT_SOURCE_ROOT):
    out=[]
    for r in _rows("04_name_catalogues/settlement_name_catalogue.csv", root):
        out.append(PlaceReference(r["source_place_code"], r["settlement_name_record_id"], r["canonical_name"], r["place_slug"], r["place_type_code"], r["settlement_scale"], r["urbanity"], r["parent_source_place_code"] or None, r["major_city_source_place_code"] or None, r["region_code"], r["region_name"], _bool(r["is_national_capital"]), _bool(r["is_regional_anchor"]), r["nickname"] or None, r["naming_status_code"], SpatialLifecycleStatus(r["feature_lifecycle_status_code"]), r["spatial_assignment_status"], r["source_dataset_id"], RecordEffectScope(r["runtime_effect_scope"]), r["record_status"]))
    return tuple(out)

def load_administrative_areas(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(AdministrativeArea(r["administrative_candidate_id"], r["source_record_id"], r["administrative_type_code"], r["canonical_name"], r["parent_source_record_id"], r["region_code"], r["boundary_status"], r["geometry_reference"] or None, SpatialLifecycleStatus(r["lifecycle_status_code"]), RecordEffectScope(r["runtime_effect_scope"]), r["source_basis"], r["candidate_status"]) for r in _rows("05_geographic_candidates/administrative_area_candidates.csv", root))

def load_feature_name_assignments(root: Path = DEFAULT_SOURCE_ROOT):
    return tuple(GeographicNameAssignment(r["assignment_candidate_id"], r["source_feature_id"], r["feature_type_code"], r["name_id"], r["canonical_name"], r["assignment_status"], GeographicNameRole.PRIMARY, _date(r["effective_from"]), _date(r["effective_to"]), r["gazette_reference"] or None, r["source_basis"], RecordEffectScope(r["runtime_effect_scope"])) for r in _rows("08_relationships/feature_name_assignment_candidates.csv", root))

__all__ = ["DEFAULT_SOURCE_ROOT", "load_feature_types", "load_naming_statuses", "load_gazette_actions", "load_feature_recognitions", "load_settlement_names", "load_places", "load_administrative_areas", "load_feature_name_assignments"]
