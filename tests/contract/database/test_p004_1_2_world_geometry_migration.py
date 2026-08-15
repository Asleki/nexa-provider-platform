from pathlib import Path

from database.migration_control.discovery import MigrationDiscovery
from database.migration_control.manifest import MigrationManifestLoader
from database.migration_control.planning import MigrationPlanner

ROOT = Path(__file__).parents[3]
MIGRATIONS = ROOT / "database/migrations"


def test_p004_world_geometry_migration_is_appended_without_rewriting_locked_artifacts():
    catalogue = MigrationManifestLoader().load(MIGRATIONS / "migration_manifest.json")
    MigrationDiscovery(MIGRATIONS).validate_catalogue(catalogue)
    plan = MigrationPlanner().create_plan(catalogue)
    item = next(x for x in plan.forward_order if x.identity.migration_id == "m004_01_02_world_geometry_authority")
    assert item.identity.sequence_number == 6
    assert plan.forward_order[5].identity.migration_id == "m004_01_02_world_geometry_authority"
    assert item.depends_on == ("m009_13_10_reference_registry_authoring",)
    for locked in (
        "m009_10_04_name_catalogue.sql",
        "m009_12_06_name_authority.sql",
        "m009_12_09_name_authority_generation.sql",
        "m009_12_12_name_authority_application.sql",
        "m009_13_10_reference_registry_authoring.sql",
    ):
        assert (MIGRATIONS / locked).is_file()


def test_p004_migration_declares_postgis_authority_and_safe_rollback():
    forward = (MIGRATIONS / "m004_01_02_world_geometry_authority.sql").read_text()
    rollback = (MIGRATIONS / "m004_01_02_world_geometry_authority_rollback.sql").read_text()
    assert "CREATE EXTENSION IF NOT EXISTS postgis" in forward
    assert "geometry(MultiPolygon, 4326)" in forward
    assert "ST_IsValid" in forward
    assert "USING gist" in forward
    assert "DROP TABLE IF EXISTS geography.boundary_publication" in rollback
    assert "DROP EXTENSION" not in rollback
