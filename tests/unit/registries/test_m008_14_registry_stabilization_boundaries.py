from pathlib import Path

REGISTRY_ROOT = Path(__file__).resolve().parents[3] / "registries"
TEST_ROOT = Path(__file__).resolve().parent


def test_all_prior_registry_milestone_boundary_tests_remain_present() -> None:
    expected = {
        "test_m008_1_import_boundaries.py",
        "test_m008_2_identifier_model_boundaries.py",
        "test_m008_3_base_registry_boundaries.py",
        "test_m008_4_registry_repository_boundaries.py",
        "test_m008_5_memory_registry_repository_boundaries.py",
        "test_m008_6_registry_factory_boundaries.py",
        "test_m008_7_registry_catalogue_boundaries.py",
        "test_m008_8_registry_lifecycle_boundaries.py",
        "test_m008_9_registry_validation_boundaries.py",
        "test_m008_10_registry_event_boundaries.py",
        "test_m008_11_registry_api_boundaries.py",
        "test_m008_12_registry_audit_boundaries.py",
        "test_m008_13_registry_test_boundaries.py",
    }
    present = {path.name for path in TEST_ROOT.glob("test_m008_*_boundaries.py")}
    assert expected.issubset(present)


def test_stabilization_suite_is_additive() -> None:
    suite = TEST_ROOT / "stabilization"
    assert suite.is_dir()
    assert {
        "test_registry_audit_result_invariants.py",
        "test_registry_audit_port_contract.py",
        "test_registry_audit_public_exports.py",
        "test_registry_api_stability_contracts.py",
    }.issubset({path.name for path in suite.glob("test_*.py")})


def test_m008_14_does_not_introduce_future_registry_features() -> None:
    forbidden = {
        "registry_metadata.py",
        "registry_capability.py",
        "data_classification_metadata.py",
        "training_eligibility_metadata.py",
        "provenance_metadata.py",
        "retention_metadata.py",
        "relationship_api.py",
        "school_registry.py",
        "bank_registry.py",
        "business_registry.py",
        "birth_registry.py",
        "sim_registry.py",
    }
    present = {path.name for path in REGISTRY_ROOT.rglob("*.py")}
    assert forbidden.isdisjoint(present)
