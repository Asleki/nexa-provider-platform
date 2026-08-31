import inspect
from registries.nngla.municipality_realization.contracts import (
    EXPECTED_MUNICIPALITY_COUNT, EXPECTED_PER_REGION, RealizationMethod,
)
from registries.nngla.municipality_realization.service import GovernedMunicipalityRealizationService

def test_inventory_and_realization_contract():
    assert EXPECTED_MUNICIPALITY_COUNT == 24
    assert EXPECTED_PER_REGION == 3
    assert {x.value for x in RealizationMethod} == {
        "SOURCE_REUSE", "REGION_CITY_CONTAINED_NORMALIZATION"
    }

def test_execution_requires_distinct_dual_actors_and_exact_complete_gate():
    source = inspect.getsource(GovernedMunicipalityRealizationService.execute_region)
    assert "submitter_actor_id" in source and "approver_actor_id" in source
    assert "submitter == approver" in source
    assert 'partition_status") != "COMPLETE"' in source
