from pathlib import Path

from backend.auth.contracts import AuthenticationStrength, IdentityType, SelectedRuntime


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / "backend" / "auth" / "admin_review_persistence").is_dir():
            return candidate
    raise AssertionError("repository root not found")


def test_c_preserves_exact_two_identity_types_and_two_semantic_runtimes() -> None:
    assert {item.value for item in IdentityType} == {"guest", "nexadevs_developer"}
    assert {item.value for item in SelectedRuntime} == {"production", "simulation"}
    assert {item.value for item in AuthenticationStrength} == {
        "guest_password",
        "developer_password_enigma",
    }


def test_c_does_not_add_admin_identity_runtime_or_authentication_strength() -> None:
    source = (_root() / "backend" / "auth" / "admin_review_persistence" / "contracts.py").read_text()
    assert "nexilabs_admin" not in source
    assert "admin_runtime" not in source
    assert "SelectedRuntime" not in source
    assert "AuthenticationStrength" not in source


def test_c_admin_adapter_remains_persistence_only_not_elevation_or_password_verification() -> None:
    source = (_root() / "backend" / "auth" / "admin_review_persistence" / "postgresql.py").read_text()
    for forbidden in (
        "verify_password(",
        "mint_session",
        "create_session",
        "elevation_ttl",
        "approve_request",
        "bootstrap_admin",
    ):
        assert forbidden not in source
    assert "read-only" in source.lower()
