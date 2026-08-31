from pathlib import Path
from database.migration_control.discovery import MigrationDiscovery
from database.migration_control.manifest import MigrationManifestLoader
from database.migration_control.planning import MigrationPlanner
ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS = ROOT / "database/migrations"

def catalogue():
    return MigrationManifestLoader().load(MIGRATIONS / "migration_manifest.json")

def test_sequence26_is_append_only_after_locked_sequence25():
    value = catalogue()
    assert MigrationDiscovery(MIGRATIONS).validate_catalogue(value) is value
    by_sequence = {x.identity.sequence_number:x for x in value.definitions}
    assert max(by_sequence) == 26
    item = by_sequence[26]
    assert item.identity.migration_id == "m006_07_11_nngla_municipality_spatial_publication"
    assert item.depends_on == ("m006_07_11_nngla_city_parent_containment_qualification",)

def test_dependency_plan_preserves_23_24_25_then_26():
    plan = MigrationPlanner().create_plan(catalogue())
    by_sequence = {x.identity.sequence_number:x for x in plan.forward_order}
    assert tuple(by_sequence[n].identity.sequence_number for n in (23,24,25,26)) == (23,24,25,26)
