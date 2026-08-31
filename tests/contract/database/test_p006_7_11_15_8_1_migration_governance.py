from pathlib import Path

from database.migration_control.discovery import MigrationDiscovery
from database.migration_control.manifest import MigrationManifestLoader
from database.migration_control.planning import MigrationPlanner


ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS = ROOT / "database/migrations"


def catalogue():
    return MigrationManifestLoader().load(MIGRATIONS / "migration_manifest.json")


def test_sequence25_is_append_only_and_depends_on_locked_city_foundation():
    value = catalogue()
    assert MigrationDiscovery(MIGRATIONS).validate_catalogue(value) is value
    by_sequence = {
        item.identity.sequence_number: item
        for item in value.definitions
    }
    tail = tuple(by_sequence[number] for number in (23, 24, 25))
    assert tuple(item.identity.sequence_number for item in tail) == (23, 24, 25)
    assert tuple(item.identity.migration_id for item in tail) == (
        "m006_07_11_nngla_region_spatial_foundation",
        "m006_07_11_nngla_city_spatial_foundation",
        "m006_07_11_nngla_city_parent_containment_qualification",
    )
    assert tail[-1].depends_on == ("m006_07_11_nngla_city_spatial_foundation",)
    assert tail[0].forward.sha256 == "7084b2359a1be8cd9d583f63d255500db15f8b3ef5130a2996d97d370aeb50ff"
    assert tail[1].forward.sha256 == "bc3be3848a63637e956ddc76eb589ee6537dbd82f9652bca1dbe8855e035ff11"


def test_sequence25_expected_object_surface_is_scoped_to_new_qualification_objects():
    item = next(
        definition
        for definition in catalogue().definitions
        if definition.identity.sequence_number == 25
    )
    assert item.expected_objects.tables == (
        "geography.nngla_city_parent_containment_qualification",
    )
    assert set(item.expected_objects.indexes) == {
        "ux_nngla_city_parent_containment_current",
        "ix_nngla_city_parent_containment_parent",
        "ix_nngla_city_parent_containment_geometry",
        "ix_nngla_city_parent_containment_source",
    }
    assert item.expected_objects.views == (
        "geography.nngla_city_parent_containment_read_v1",
    )
    assert item.expected_objects.functions == ()


def test_dependency_plan_ends_in_sequence25_without_renumbering_23_or_24():
    plan = MigrationPlanner().create_plan(catalogue())
    by_sequence = {
        item.identity.sequence_number: item
        for item in plan.forward_order
    }
    assert tuple(
        by_sequence[number].identity.sequence_number
        for number in (23, 24, 25)
    ) == (23, 24, 25)
