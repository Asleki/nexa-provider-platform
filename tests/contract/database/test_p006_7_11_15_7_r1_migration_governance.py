"""P006.7.11.15.7_R1 — migration-governance compatibility regression."""
from pathlib import Path

from database.migration_control.discovery import MigrationDiscovery
from database.migration_control.manifest import MigrationManifestLoader
from database.migration_control.planning import MigrationPlanner


ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS = ROOT / "database" / "migrations"


def _catalogue():
    return MigrationManifestLoader().load(MIGRATIONS / "migration_manifest.json")


def test_region_and_city_foundations_are_governed_manifest_artifacts():
    catalogue = _catalogue()
    assert MigrationDiscovery(MIGRATIONS).validate_catalogue(catalogue) is catalogue
    tail = catalogue.definitions[-2:]
    assert tuple(item.identity.migration_id for item in tail) == (
        "m006_07_11_nngla_region_spatial_foundation",
        "m006_07_11_nngla_city_spatial_foundation",
    )
    assert tuple(item.identity.sequence_number for item in tail) == (23, 24)


def test_region_foundation_remains_independent_from_delivery3_authority_adoption():
    catalogue = _catalogue()
    by_id = catalogue.by_id()
    region = by_id["m006_07_11_nngla_region_spatial_foundation"]
    city = by_id["m006_07_11_nngla_city_spatial_foundation"]
    assert region.depends_on == ("m006_07_11_nngla_identity_places_runtime",)
    assert city.depends_on == ("m006_07_11_nngla_region_spatial_foundation",)
    assert "m006_07_11_nngla_administrative_authority_adoption" not in region.depends_on


def test_region_and_city_rollbacks_are_non_cascading_and_scoped():
    for stem, required in (
        (
            "m006_07_11_nngla_region_spatial_foundation",
            (
                "drop view if exists geography.nngla_region_public_read_v1;",
                "drop table if exists geography.nngla_region_publication;",
                "drop table if exists geography.nngla_region_geometry_record;",
            ),
        ),
        (
            "m006_07_11_nngla_city_spatial_foundation",
            (
                "drop view if exists geography.nngla_city_public_read_v1;",
                "drop table if exists geography.nngla_city_publication;",
                "drop table if exists geography.nngla_city_geometry_record;",
            ),
        ),
    ):
        text = (MIGRATIONS / f"{stem}_rollback.sql").read_text(encoding="utf-8").lower()
        assert text.startswith("begin;")
        assert text.rstrip().endswith("commit;")
        assert " cascade" not in text
        for token in required:
            assert token in text


def test_dependency_plan_keeps_new_branch_deterministic():
    plan = MigrationPlanner().create_plan(_catalogue())
    ids = tuple(item.identity.migration_id for item in plan.forward_order)
    assert ids[-2:] == (
        "m006_07_11_nngla_region_spatial_foundation",
        "m006_07_11_nngla_city_spatial_foundation",
    )
