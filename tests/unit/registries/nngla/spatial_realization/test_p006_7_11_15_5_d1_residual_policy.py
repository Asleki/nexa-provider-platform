from registries.nngla.spatial_realization.residual_policy import (
    MicroAssignmentEvidence,
    delivery1_micro_assignment_eligible,
)


def test_delivery1_micro_assignment_requires_more_than_r3_area_and_ratio_thresholds():
    base=dict(area_km2=1e-7,area_ratio=1e-9,difference_dimension=2)
    assert not delivery1_micro_assignment_eligible(
        **base,
        evidence=MicroAssignmentEvidence(0.1,True,True,False,None),
    )
    assert delivery1_micro_assignment_eligible(
        **base,
        evidence=MicroAssignmentEvidence(0.1,True,True,False,0.5),
    )
    assert not delivery1_micro_assignment_eligible(
        **base,
        evidence=MicroAssignmentEvidence(0.6,True,True,False,0.5),
    )
    assert not delivery1_micro_assignment_eligible(
        **base,
        evidence=MicroAssignmentEvidence(0.1,False,True,False,0.5),
    )
    assert not delivery1_micro_assignment_eligible(
        **base,
        evidence=MicroAssignmentEvidence(0.1,True,False,False,0.5),
    )
    assert not delivery1_micro_assignment_eligible(
        **base,
        evidence=MicroAssignmentEvidence(0.1,True,True,True,0.5),
    )


def test_delivery1_material_residual_never_becomes_auto_eligible_from_morphology_fields():
    assert not delivery1_micro_assignment_eligible(
        area_km2=1.1332812267,
        area_ratio=1.677e-5,
        difference_dimension=2,
        evidence=MicroAssignmentEvidence(0.01,True,True,False,1.0),
    )
