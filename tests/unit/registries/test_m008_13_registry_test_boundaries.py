from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REGISTRY_TEST_ROOT = ROOT / "tests" / "unit" / "registries"


def test_all_previous_registry_milestone_boundary_tests_remain_present():
    expected = {
        f"test_m008_{milestone}_" for milestone in range(1, 10)
    }
    names = {path.name for path in REGISTRY_TEST_ROOT.glob("test_m008_*.py")}
    for prefix in expected:
        assert any(name.startswith(prefix) for name in names), prefix
    assert "test_m008_10_registry_event_boundaries.py" in names
    assert "test_m008_11_registry_api_boundaries.py" in names
    assert "test_m008_12_registry_audit_boundaries.py" in names


def test_m008_13_adds_tests_only_and_does_not_create_test_specific_production_modules():
    registries_root = ROOT / "registries"
    forbidden_fragments = ("system_test", "integration_test", "test_helper", "m008_13")
    offending = [
        path.relative_to(ROOT).as_posix()
        for path in registries_root.rglob("*.py")
        if any(fragment in path.name.lower() for fragment in forbidden_fragments)
    ]
    assert offending == []


def test_registry_integration_suite_exists_as_additive_test_package():
    integration = REGISTRY_TEST_ROOT / "integration"
    expected = {
        "test_registry_end_to_end_workflows.py",
        "test_registry_failure_safety.py",
        "test_registry_determinism.py",
    }
    assert integration.is_dir()
    assert expected.issubset({path.name for path in integration.glob("test_*.py")})
