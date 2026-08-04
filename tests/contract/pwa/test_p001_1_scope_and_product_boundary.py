"""Contract tests for P001.1 — PWA Scope and Product Boundary."""

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

DOCUMENT = (
    REPOSITORY_ROOT
    / "docs"
    / "pwa"
    / "PWA-001-scope-and-product-boundary.md"
)


def _document_text() -> str:
    """Return the authoritative PWA-001 document text."""

    return DOCUMENT.read_text(encoding="utf-8")


def _normalized_document_text() -> str:
    """Return document text with Markdown line wrapping normalized."""

    return " ".join(_document_text().split())


def test_scope_document_exists() -> None:
    assert DOCUMENT.is_file()


def test_document_identity_and_milestone_are_declared() -> None:
    text = _document_text()

    assert "# PWA-001 — NexiLabs PWA Scope and Product Boundary" in text
    assert "| Document ID | `PWA-001` |" in text
    assert "| Roadmap milestone | `P001.1 — PWA Scope and Product Boundary` |" in text
    assert "| Status | Normative foundation |" in text


def test_initial_scope_is_novegeo_map_and_world_visualisation() -> None:
    text = _document_text()

    assert "| Initial product scope | NoveGeo map and world visualisation |" in text
    assert "Its first operational purpose is to present, inspect, and interact with the" in text
    assert "simulated geography and evolving world state of NoveGeo." in text
    assert "The initial product is limited to the NoveGeo map" in text


def test_aws_is_the_runtime_hosting_target() -> None:
    text = _document_text()

    assert "| Runtime hosting target | AWS |" in text
    assert "AWS is the runtime hosting target for the PWA." in text
    assert "GitHub remains the source-control" in text


def test_npp_is_the_authoritative_backend() -> None:
    text = _document_text()

    assert "| Authoritative backend | Nexa Provider Platform (NPP) |" in text
    assert "NPP is the authoritative provider platform." in text
    assert "The PWA is a presentation and" in text
    assert "interaction client." in text


def test_direct_postgresql_access_is_prohibited() -> None:
    text = _document_text()

    assert "A browser client must never connect directly to PostgreSQL." in text
    assert "browser JavaScript → PostgreSQL / Amazon RDS" in text
    assert "browser PWA → HTTPS API → NPP service → PostgreSQL repository" in text


def test_https_and_versioned_api_boundary_are_required() -> None:
    text = _normalized_document_text()

    assert "versioned and secured API boundary" in text
    assert "use HTTPS for network access;" in text
    assert "secure, versioned API consumption" in text


def test_simulation_and_production_are_distinct() -> None:
    text = _document_text()

    assert "Simulation and production are distinct execution contexts." in text
    assert "The runtime mode" in text
    assert "must be explicit in configuration" in text
    assert "merge simulation and production records into one unlabelled result" in text
    assert "promote simulation data into production" in text


def test_pwa_is_not_a_registry_authority_or_system_of_record() -> None:
    text = _normalized_document_text()

    assert "accidental registry authority" in text
    assert "The PWA owns presentation state only" in text
    assert (
        "Cached data is a local copy for presentation and offline continuity. "
        "It is not the system of record."
    ) in text


def test_nexapos_alpha_boundary_is_explicit() -> None:
    text = _document_text()

    assert "## 8. Relationship to NexaPOS Alpha" in text
    assert "NexaPOS Alpha remains an independent operational application." in text
    assert "P001.1 does not" in text
    assert "integrate NexaPOS Alpha" in text
    assert "The PWA must not directly read NexaPOS local storage" in text


def test_future_registry_interfaces_are_deferred() -> None:
    text = _document_text()

    assert "## 12. Future registry extension model" in text
    assert "Later registries may expose safe map references" in text
    assert "The owning registry retains legal identity, lifecycle, policy" in text
    assert "citizen, birth, household, business, school, healthcare, banking" in text
    assert "other operational registry interfaces" in text


def test_stable_semantic_identifiers_are_reserved() -> None:
    text = _document_text()

    required_identifiers = (
        "`map_feature_id`",
        "`map_layer_id`",
        "`world_state_version`",
        "`dataset_id`",
        "`location_id`",
        "`registry_record_id`",
        "`event_id`",
        "`simulation_scenario_id`",
        "`runtime_mode`",
        "`request_id`",
        "`correlation_id`",
        "`citizen_id`",
        "`business_id`",
        "`institution_id`",
        "`estate_id`",
    )

    for identifier in required_identifiers:
        assert identifier in text

    assert "ambiguous generic" in text
    assert "`id` field" in text


def test_cross_roadmap_completion_is_not_automatic() -> None:
    text = _document_text()

    assert "## 13. Cross-roadmap completion rule" in text
    assert "must never automatically mark an NPP record complete" in text
    assert "an NPP milestone does not automatically complete a PWA milestone" in text


def test_frontend_secrets_are_prohibited() -> None:
    text = _normalized_document_text()

    prohibited_secret_terms = (
        "AWS access key",
        "secret key",
        "session token",
        "database password",
        "private service credential",
    )

    for term in prohibited_secret_terms:
        assert term in text

    assert (
        "No AWS access key, secret key, session token, database password, "
        "or private service credential may be embedded in frontend source"
    ) in text


def test_privacy_can_become_stricter_without_replacing_identity() -> None:
    text = _normalized_document_text()

    assert (
        "support stricter privacy policies without replacing stable identities;"
        in text
    )
    assert "Stable identifiers may remain unchanged" in text
    assert "more restrictive, masked, aggregated, or role-dependent" in text


def test_offline_cache_is_not_authoritative() -> None:
    text = _document_text()

    assert "Cached data is a local copy for presentation and offline continuity." in text
    assert "It is not" in text
    assert "the system of record." in text
    assert "treat stale cached state as current authoritative state" in text
    assert "merge data across runtime modes" in text


def test_current_exclusions_are_explicit() -> None:
    text = _document_text()

    assert "## 16. Current exclusions" in text
    assert "frontend application directories or application bootstrap;" in text
    assert "AWS infrastructure or deployment;" in text
    assert "direct PostgreSQL access;" in text
    assert "NexaPOS integration;" in text
    assert "Name Catalogue authoring from the browser;" in text
    assert "claims that NoveGeo is a real Earth jurisdiction." in text


def test_reserved_and_deferred_capabilities_are_distinct() -> None:
    text = _document_text()

    assert "## 17. Reserved capabilities" in text
    assert "Reservation is not implementation and does not imply readiness." in text
    assert "## 18. Deferred capabilities" in text
    assert "implemented only by their owning later milestones" in text


def test_acceptance_criteria_and_guiding_principle_are_present() -> None:
    text = _document_text()

    assert "## 19. Acceptance criteria" in text
    assert "P001.1 is acceptable only when:" in text
    assert "## 20. Guiding principle" in text
    assert "The NexiLabs PWA presents the simulated world" in text
    assert "remain authoritative for the facts, identities, rules, events, and decisions" in text
