from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
METADATA_TESTS = ROOT / "tests" / "unit" / "registries" / "metadata"


def test_m008_15_7_appends_tests_without_removing_earlier_metadata_tests():
    required_existing = {
        "test_registry_metadata_profile.py",
        "test_registry_metadata_validator.py",
        "test_registry_metadata_exports.py",
        "test_registry_capability.py",
        "test_registry_data_classification.py",
        "test_registry_training_eligibility.py",
        "test_registry_provenance.py",
        "test_registry_retention.py",
    }
    actual = {path.name for path in METADATA_TESTS.glob("test_*.py")}
    assert required_existing <= actual


def test_m008_15_7_does_not_introduce_deferred_domain_engines():
    # The names package was deferred during M008.15.7 and is now explicitly
    # authorised by M009.1. Other deferred domain engines remain absent.
    forbidden = (
        ROOT / "registries" / "marriages",
        ROOT / "registries" / "jurisdictions",
    )
    assert all(not path.exists() for path in forbidden)


def test_metadata_profile_remains_the_only_updated_production_target():
    profile = ROOT / "registries" / "metadata" / "registry_metadata_profile.py"
    assert profile.exists()
    assert "def from_dict" in profile.read_text(encoding="utf-8")


def test_m009_1_now_authorises_the_previously_deferred_names_package():
    names = ROOT / "registries" / "names"
    assert names.is_dir()
    assert (names / "canonical_name.py").exists()
