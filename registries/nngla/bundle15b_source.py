"""Read-only P006.7.5/P006.7.6 governed source snapshot loader."""
from __future__ import annotations
import csv
from datetime import date, datetime
from pathlib import Path
from registries.country.operating_context import RecordEffectScope
from .geodesy import CoordinateReferenceSystemDefinition, GeometryTypeDefinition, SurveyAccuracyClass
from .geometry_versions import GeometryVersionRecord
from .survey import SurveyControlPointCandidate
from .roads import RoadClassificationDefinition, RoadReferenceCandidate
from .addresses import AddressReferenceCandidate

DEFAULT_SOURCE_ROOT=Path(__file__).resolve().parents[2]/"data"/"novegeo"/"nngla"/"geometry-roads-addresses"/"source"
def _rows(rel,root=DEFAULT_SOURCE_ROOT):
    with (root/rel).open('r',encoding='utf-8-sig',newline='') as f: return list(csv.DictReader(f))
def _bool(v):
    if str(v).lower() not in {'true','false'}: raise ValueError(f'invalid boolean {v!r}')
    return str(v).lower()=='true'
def _date(v): return date.fromisoformat(v) if v else None
def _dt(v): return datetime.fromisoformat(v.replace('Z','+00:00')) if v else None
def _int(v): return int(v) if v else None

def load_crs_definitions(root=DEFAULT_SOURCE_ROOT):
    return tuple(CoordinateReferenceSystemDefinition(r['crs_code'],r['authority_name'],r['authority_code'],r['canonical_name'],r['axis_order'],r['horizontal_unit'],r['vertical_unit'],_bool(r['is_geographic']),_bool(r['is_default_novegeo']),r['status'],_date(r['effective_from']),_date(r['effective_to']),r['notes']) for r in _rows('02_controlled_codes/coordinate_reference_systems.csv',root))

def load_geometry_types(root=DEFAULT_SOURCE_ROOT):
    return tuple(GeometryTypeDefinition(r['geometry_type_code'],r['canonical_label'],r['ogc_geometry_type'],int(r['dimension']),_bool(r['supports_multiple_parts']),_bool(r['supports_ring']),_bool(r['supports_linear_reference']),r['description'],r['status']) for r in _rows('02_controlled_codes/geometry_type_codes.csv',root))

def load_survey_accuracy_classes(root=DEFAULT_SOURCE_ROOT):
    return tuple(SurveyAccuracyClass(r['accuracy_class_code'],r['canonical_label'],r['usage_scope'],r['horizontal_accuracy_rule'],r['vertical_accuracy_rule'],_bool(r['legal_boundary_eligible']),_bool(r['control_point_eligible']),_bool(r['informational_only']),_bool(r['requires_instrument_record']),_bool(r['requires_surveyor_approval']),r['status'],r['notes']) for r in _rows('02_controlled_codes/survey_accuracy_classes.csv',root))

def load_road_classifications(root=DEFAULT_SOURCE_ROOT):
    return tuple(RoadClassificationDefinition(r['road_class_code'],r['canonical_label'],r['administrative_level'],r['access_scope'],r['intended_function'],_bool(r['nameable']),_bool(r['addressable']),_bool(r['parcel_access_eligible']),r['status'],r['description']) for r in _rows('02_controlled_codes/road_classification_codes.csv',root))

def load_geometry_versions(root=DEFAULT_SOURCE_ROOT):
    return tuple(GeometryVersionRecord(r['geometry_version_candidate_id'],r['subject_type'],r['subject_id'],r['geometry_role_code'],r['source_geometry_id'],r['source_dataset_id'],r['source_version'],r['geometry_type_code'],r['crs_code'],r['authoritative_level'],_int(r['vertex_count']),_int(r['part_count']),_date(r['valid_from']),_date(r['valid_to']),r['supersedes_geometry_id'] or None,r['superseded_by_geometry_id'] or None,r['qualification_status'],r['publication_status'],r['checksum_sha256'],r['source_path_reference'],RecordEffectScope(r['runtime_effect_scope']),r['notes']) for r in _rows('05_geographic_candidates/geometry_version_candidates.csv',root))

def load_survey_control_points(root=DEFAULT_SOURCE_ROOT):
    return tuple(SurveyControlPointCandidate(r['survey_control_candidate_id'],r['source_point_id'],r['candidate_role'],float(r['longitude']),float(r['latitude']),r['crs_code'],r['accuracy_class_code'],r['qualification_status'],r['source_basis']) for r in _rows('05_geographic_candidates/survey_control_point_candidates.csv',root))

def load_road_candidates(root=DEFAULT_SOURCE_ROOT):
    return tuple(RoadReferenceCandidate(r['road_candidate_id'],r['road_name_id'],r['canonical_name'],r['road_class_code'],r['source_name_family'],r['planning_status'],r['geometry_status'],r['geometry_reference'] or None,_bool(r['addressing_eligible']),r['region_code'] or None,r['source_basis'],RecordEffectScope(r['runtime_effect_scope'])) for r in _rows('06_roads_addresses/road_reference_candidates.csv',root))

def load_address_candidates(root=DEFAULT_SOURCE_ROOT):
    return tuple(AddressReferenceCandidate(r['address_candidate_id'],r['street_id'] or None,r['address_series'] or None,r['premise_sequence'] or None,r['unit_designator'] or None,r['display_address_number'] or None,r['place_id'] or None,r['administrative_area_id'] or None,r['parcel_id'] or None,r['allocation_status'],r['address_status'],_dt(r['reserved_at']),_dt(r['assigned_at']),_dt(r['retired_at']),r['source_reference'],RecordEffectScope(r['runtime_effect_scope'])) for r in _rows('06_roads_addresses/address_reference_candidates.csv',root))

__all__=['DEFAULT_SOURCE_ROOT','load_crs_definitions','load_geometry_types','load_survey_accuracy_classes','load_road_classifications','load_geometry_versions','load_survey_control_points','load_road_candidates','load_address_candidates']
