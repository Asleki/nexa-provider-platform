from pathlib import Path

from database.migration_control.discovery import MigrationDiscovery
from database.migration_control.manifest import MigrationManifestLoader
from database.migration_control.planning import MigrationPlanner


ROOT = Path(__file__).parents[3]
MIGRATIONS = ROOT / "database/migrations"


def test_m009_13_manifest_approves_complete_current_migration_chain():
    catalogue = MigrationManifestLoader().load(MIGRATIONS / "migration_manifest.json")
    MigrationDiscovery(MIGRATIONS).validate_catalogue(catalogue)
    plan = MigrationPlanner().create_plan(catalogue)
    assert plan.migration_count == 10
    assert sum(len(item.expected_objects.tables) for item in catalogue.definitions) == 51
    assert sum(len(item.expected_objects.indexes) for item in catalogue.definitions) == 20
    assert catalogue.definitions[0].expected_objects.schemas == ("reference",)


def test_m009_13_manifest_records_embedded_transaction_policy_for_locked_sql():
    catalogue = MigrationManifestLoader().load(MIGRATIONS / "migration_manifest.json")
    assert all(item.forward.transaction_policy == "embedded" for item in catalogue.definitions)
    assert all(item.rollback.transaction_policy == "embedded" for item in catalogue.definitions)


def test_m009_13_10_reference_authoring_is_appended_to_locked_chain():
    catalogue = MigrationManifestLoader().load(MIGRATIONS / "migration_manifest.json")
    item = next(item for item in catalogue.definitions if item.identity.migration_id == "m009_13_10_reference_registry_authoring")
    assert item.identity.migration_id == "m009_13_10_reference_registry_authoring"
    assert item.identity.sequence_number == 5
    assert item.depends_on == ("m009_12_12_name_authority_application",)
