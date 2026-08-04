"""Contract tests for P001.1 — PWA Scope and Product Boundary."""
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENT = REPOSITORY_ROOT / "docs" / "pwa" / "PWA-001-scope-and-product-boundary.md"


def _document_text() -> str:
    return DOCUMENT.read_text(encoding="utf-8")


def test_scope_document_exists() -> None:
    assert DOCUMENT.is_file()


def test_document_identity_and_milestone_are_declared() -> None:
    text = _document_text()
    assert "PWA-001" in text
    assert "P001.1 — PWA Scope and Product Boundary" in text


def test_initial_scope_is_novegeo_map_and_world_visualisation() -> None:
    text = _document_text()
    assert "NoveGeo map and world visualisation" in text
    assert "first operational purpose" in text


def test_aws_is_the_runtime_hosting_target() -> None:
    text = _document_text()
    assert "AWS is the runtime hosting target" in text
    assert "GitHub remains the source-control" in text


def test_npp_is_the_authoritative_backend() -> None:
    text = _document_text()
    assert "NPP is the authoritative provider platform" in text
    assert "The PWA is a presentation and\ninteraction client" in text


def test_direct_postgresql_access_is_prohibited() -> None:
    text = _document_text()
    assert "A browser client must never connect directly to PostgreSQL" in text
    assert "browser PWA → HTTPS API → NPP service → PostgreSQL repository" in text
    assert "port `5432`" in text


def test_https_and_versioned_api_boundary_are_required() -> None:
    text = _document_text()
    assert "PWA\n    ↓ HTTPS\nversioned and secured API boundary" in text
    assert "use HTTPS for network access" in text


def test_simulation_and_production_are_distinct() -> None:
    text = _document_text()
    assert "Simulation and production are distinct execution contexts" in text
    assert "merge simulation and production records" in text
    assert "promote simulation data into production" in text


def test_pwa_is_not_a_registry_authority_or_system_of_record() -> None:
    text = _document_text()
    assert "does not become its\nowner" in text
    assert "It is not\nthe system of record" in text
    assert "The PWA owns presentation state only" in text


def test_nexapos_alpha_boundary_is_explicit() -> None:
    text = _document_text()
    assert "NexaPOS Alpha remains an independent operational application" in text
    assert "does not change its contracts" in text
    assert "must not directly read NexaPOS local storage" in text


def test_future_registry_interfaces_are_deferred() -> None:
    text = _document_text()
    for phrase in (
        "Citizen Registry",
        "Business Registry",
        "Education Registry",
        "Healthcare Registry",
        "Banking Registry",
        "Geography Registry",
    ):
        assert phrase in text
    assert "after their authoritative systems exist" in text


def test_stable_semantic_identifiers_are_reserved() -> None:
    text = _document_text()
    for identifier in (
        "`map_feature_id`",
        "`map_layer_id`",
        "`world_state_version`",
        "`dataset_id`",
        "`location_id`",
        "`registry_record_id`",
        "`event_id`",
        "`runtime_mode`",
    ):
        assert identifier in text
    assert "ambiguous generic\n`id` field" in text


def test_cross_roadmap_completion_is_not_automatic() -> None:
    text = _document_text()
    assert "must never automatically mark an NPP record complete" in text
    assert "separate deliberate update to the NPP canonical roadmap" in text


def test_frontend_secrets_are_prohibited() -> None:
    text = _document_text()
    assert "No AWS access key, secret key, session token, database password" in text
    assert "credentials and secrets outside public frontend code" in text


def test_privacy_can_become_stricter_without_replacing_identity() -> None:
    text = _document_text()
    assert "support stricter privacy policies without replacing stable identities" in text
    assert "Stable identifiers may remain unchanged" in text


def test_acceptance_criteria_and_guiding_principle_are_present() -> None:
    text = _document_text()
    assert "## 19. Acceptance criteria" in text
    assert "## 20. Guiding principle" in text
    assert "The NexiLabs PWA presents the simulated world" in text
