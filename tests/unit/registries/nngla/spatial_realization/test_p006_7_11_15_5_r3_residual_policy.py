from registries.nngla.spatial_realization.residual_policy import (
    MAX_AUTOMATIC_RESIDUAL_KM2,
    MAX_AUTOMATIC_RESIDUAL_RATIO,
    RepairEligibility,
    ResidualClass,
    context_decision,
    executable_decision,
)


def test_zero_area_or_subpolygon_dimension_remains_raw_failure_but_is_micro_repair_eligible():
    decision=executable_decision(area_km2=0.0,area_ratio=0.0,difference_dimension=1)
    assert decision.residual_class is ResidualClass.ZERO_AREA_BOUNDARY_RESIDUAL
    assert decision.repair_eligibility is RepairEligibility.AUTOMATIC_SUCCESSOR_ELIGIBLE


def test_micro_residual_requires_both_absolute_and_relative_envelopes():
    inside=executable_decision(
        area_km2=MAX_AUTOMATIC_RESIDUAL_KM2,
        area_ratio=MAX_AUTOMATIC_RESIDUAL_RATIO,
        difference_dimension=2,
    )
    assert inside.residual_class is ResidualClass.MICRO_BOUNDARY_RESIDUAL
    assert inside.repair_eligibility is RepairEligibility.AUTOMATIC_SUCCESSOR_ELIGIBLE
    absolute_fail=executable_decision(area_km2=MAX_AUTOMATIC_RESIDUAL_KM2+1e-9,area_ratio=1e-9,difference_dimension=2)
    ratio_fail=executable_decision(area_km2=1e-6,area_ratio=MAX_AUTOMATIC_RESIDUAL_RATIO+1e-12,difference_dimension=2)
    assert absolute_fail.repair_eligibility is RepairEligibility.GOVERNED_STRUCTURAL_REVIEW_REQUIRED
    assert ratio_fail.repair_eligibility is RepairEligibility.GOVERNED_STRUCTURAL_REVIEW_REQUIRED


def test_live_observed_northgate_and_silvermere_scale_cases_remain_structural_review():
    northgate=executable_decision(area_km2=1.1332812266937642,area_ratio=1.67715676794e-5,difference_dimension=2)
    silvermere=executable_decision(area_km2=0.010038004612870964,area_ratio=1.38776734203e-7,difference_dimension=2)
    assert northgate.repair_eligibility is RepairEligibility.GOVERNED_STRUCTURAL_REVIEW_REQUIRED
    assert silvermere.repair_eligibility is RepairEligibility.GOVERNED_STRUCTURAL_REVIEW_REQUIRED


def test_validation_context_never_becomes_automatic_mutation():
    decision=context_decision(area_km2=0.000697163921987197,area_ratio=2.0863582983301383e-9,difference_dimension=2)
    assert decision.residual_class is ResidualClass.MICRO_BOUNDARY_RESIDUAL
    assert decision.repair_eligibility is RepairEligibility.CONTEXT_ONLY
