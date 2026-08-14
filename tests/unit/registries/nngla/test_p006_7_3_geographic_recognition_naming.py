import pytest
from registries.country.operating_context import RecordEffectScope
from registries.nngla.bundle15a_source import load_feature_types, load_feature_recognitions, load_naming_statuses, load_settlement_names, load_feature_name_assignments
from registries.nngla.geographic_features import GeographicOriginClass, MemoryGeographicFeatureRepository
from registries.nngla.geographic_names import MemoryGeographicNameRepository
from registries.nngla.name_assignments import MemoryNameAssignmentRepository

def test_natural_features_are_recognizable_but_not_creatable():
    natural=[x for x in load_feature_types() if x.origin_class is GeographicOriginClass.NATURAL]
    assert natural
    assert all(x.nngla_recognizable for x in natural)
    assert all(not x.nngla_creatable for x in natural)

def test_source_backed_feature_recognition_is_populated_and_traceable():
    records=load_feature_recognitions(); repo=MemoryGeographicFeatureRepository()
    assert len(records)==21
    for r in records: repo.add(r)
    river=repo.by_source('river:novegeo:r000001')
    assert river is not None
    assert river.feature_type_code=='RIVER'
    assert river.source_geometry_reference
    assert river.candidate_status=='READY_FOR_NNGLA_RECOGNITION'

def test_geographic_names_are_shared_reference_and_proposed_settlements_are_not_public_official():
    names=load_settlement_names(); statuses={x.naming_status_code:x for x in load_naming_statuses()}
    assert len(names)==700
    assert all(n.runtime_effect_scope is RecordEffectScope.SHARED_REFERENCE for n in names)
    assert statuses['PROPOSED'].can_display_publicly is False
    assert statuses['ACTIVE_OFFICIAL'].can_display_publicly is True
    repo=MemoryGeographicNameRepository(); repo.add(names[0]); assert repo.get(names[0].name_id)==names[0]

def test_feature_name_assignments_remain_proposed_ungazetted_and_separate_from_feature_identity():
    assignments=load_feature_name_assignments(); repo=MemoryNameAssignmentRepository()
    assert len(assignments)==20
    for a in assignments: repo.add(a)
    first=assignments[0]
    assert first.subject_id=='river:novegeo:r000001'
    assert first.name_id=='NG-NAM-RIV-000001'
    assert first.subject_id != first.name_id
    assert first.assignment_status=='PROPOSED_UNGAZETTED'
    assert first.gazette_reference is None
    assert first.is_publicly_official is False
