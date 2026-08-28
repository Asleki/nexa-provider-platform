import pytest
from registries.nngla.spatial_realization.authority_adoption.contracts import FabricCompletenessStatus, PrecisionMode
from registries.nngla.spatial_realization.authority_adoption.fabric_completeness import completeness_report
from registries.nngla.spatial_realization.authority_adoption.precision_normalization import governed_common_precision_policy, numerical_residue


def test_numerical_residue_requires_governed_precision_and_exact_zero_after_normalization():
    policy = governed_common_precision_policy(policy_id="precision:nngla:v1", grid_size_degrees=1e-9, evidence_reference="decision:p1")
    assert numerical_residue(raw_value=1.534e-7, evaluated_value=0.0, policy=policy)
    assert not numerical_residue(raw_value=1.534e-7, evaluated_value=1e-12, policy=policy)


def test_fabric_complete_is_separate_from_city_feature_qualification():
    partial = completeness_report(parent_administrative_area_id="NG-ADM-000032", expected_child_count=8,
        qualified_child_count=2, published_child_count=2, gap_m2=1.0, positive_overlap_m2=0.0, evidence_material={"x":1})
    assert partial.status is FabricCompletenessStatus.PARTIAL
    complete = completeness_report(parent_administrative_area_id="NG-ADM-000032", expected_child_count=8,
        qualified_child_count=8, published_child_count=8, gap_m2=0.0, positive_overlap_m2=0.0, evidence_material={"x":2})
    assert complete.status is FabricCompletenessStatus.COMPLETE
