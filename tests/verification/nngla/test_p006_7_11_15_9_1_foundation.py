from registries.nngla.municipality_realization.contracts import PLAN_ID, PLAN_VERSION, REALIZATION_VERSION

def test_municipality_foundation_versions_are_explicit():
    assert PLAN_ID == "p006.7.11.15.9.1-governed-municipality-realization"
    assert PLAN_VERSION == 1
    assert REALIZATION_VERSION == 1
