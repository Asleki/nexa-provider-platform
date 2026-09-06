"""P006.7.11.7.20 remediation — governed operational migration closure.

This test suite is additive. It verifies that the already-approved Bundle 17H-17O
PostgreSQL contracts are deployable through the existing migration-control system
without changing locked NNGLA domain implementations or canonical identities.
"""
from __future__ import annotations

from pathlib import Path

from database.migration_control.discovery import MigrationDiscovery
from database.migration_control.manifest import MigrationManifestLoader
from database.migration_control.planning import MigrationPlanner
from registries.nngla.spatial_fabric.bundle17h.postgresql_contract import load_schema17h_sql, qualify_schema17h_sql
from registries.nngla.spatial_fabric.bundle17i.postgresql_contract import load_schema17i_sql, qualify_schema17i_sql
from registries.nngla.spatial_fabric.bundle17j.postgresql_contract import load_schema17j_sql, qualify_schema17j_sql
from registries.nngla.spatial_fabric.bundle17k.postgresql_contract import load_schema17k_sql, qualify_schema17k_sql
from registries.nngla.spatial_fabric.bundle17l.postgresql_contract import load_schema17l_sql, qualify_schema17l_sql
from registries.nngla.spatial_fabric.bundle17m.postgresql_contract import load_schema17m_sql, qualify_schema17m_sql
from registries.nngla.spatial_fabric.bundle17n.postgresql_contract import load_schema17n_sql, qualify_schema17n_sql
from registries.nngla.spatial_fabric.bundle17o.postgresql_contract import load_schema17o_sql, qualify_schema17o_sql

ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS = ROOT / "database" / "migrations"
SCHEMAS = ROOT / "database" / "schemas"

TAIL = (
    ("nngla_smart_addressing_sites.sql", "m006_07_11_nngla_smart_addressing_sites"),
    ("nngla_title_reservations_state_land_candidates.sql", "m006_07_11_nngla_title_reservations_state_land_candidates"),
    ("nngla_allocator_concurrency_recovery.sql", "m006_07_11_nngla_allocator_concurrency_recovery"),
    ("nngla_geometry_change_lifecycle.sql", "m006_07_11_nngla_geometry_change_lifecycle"),
    ("nngla_feature_recognition_lifecycle.sql", "m006_07_11_nngla_feature_recognition_lifecycle"),
    ("nngla_geographic_naming_gazette.sql", "m006_07_11_nngla_geographic_naming_gazette"),
    ("nngla_runtime_command_services.sql", "m006_07_11_nngla_runtime_command_services"),
    ("nngla_spatial_query_read_models.sql", "m006_07_11_nngla_spatial_query_read_models"),
)

LOCKED_PREFIX = (
    "m009_10_04_name_catalogue",
    "m009_12_06_name_authority",
    "m009_12_09_name_authority_generation",
    "m009_12_12_name_authority_application",
    "m009_13_10_reference_registry_authoring",
    "m004_01_02_world_geometry_authority",
    "m006_07_11_nngla_execution_foundation",
    "m006_07_11_nngla_identity_places_runtime",
    "m006_07_11_nngla_geometry_roads_runtime",
    "m006_07_11_nngla_cadastre_runtime",
)

LOCKED_BASE_TABLES = (
    "nngla_spatial_feature", "nngla_geometry_version", "nngla_geographic_name",
    "nngla_name_assignment", "nngla_place_reference", "nngla_administrative_area",
    "nngla_geometry_authority_record", "nngla_road", "nngla_addressable_site",
    "nngla_address", "nngla_parcel", "nngla_title", "nngla_state_land",
)


def _catalogue():
    return MigrationManifestLoader().load(MIGRATIONS / "migration_manifest.json")


def test_manifest_extends_locked_ten_entry_prefix_without_renumbering():
    catalogue = _catalogue()
    ids = tuple(item.identity.migration_id for item in catalogue.definitions)
    assert ids[:10] == LOCKED_PREFIX
    assert ids[10:18] == tuple(stem for _, stem in TAIL)
    assert tuple(item.identity.sequence_number for item in catalogue.definitions[:18]) == tuple(range(1, 19))
    # Preserve the complete historical M006.7.11 migration ownership through
    # sequence 30 and the exact P006.UI.10.2 / M006.10.2 migration-31 successor.
    # Later governed migrations may append after this immutable historical prefix.
    assert all(item.identity.milestone_id == "M006.7.11" for item in catalogue.definitions[10:30])
    assert ids[30] == "m006_10_02_nexilabs_account_credential_authority"
    account_successor = catalogue.definitions[30]
    assert account_successor.identity.sequence_number == 31
    assert account_successor.identity.milestone_id == "M006.10.2"
    assert account_successor.depends_on == (
        "m006_07_11_nngla_municipality_public_read_qualification_admission_correction",
    )
    assert catalogue.definitions[10].depends_on == (LOCKED_PREFIX[-1],)
    # Preserve the exact historical operational chain through Delivery 3.
    # Later additive migrations may branch from the earliest stable contract
    # they actually require; they must not acquire a false Delivery-3
    # architectural dependency merely to satisfy this historical lock.
    locked_operational_chain = catalogue.definitions[10:22]
    for previous, current in zip(locked_operational_chain, locked_operational_chain[1:]):
        assert current.depends_on == (previous.identity.migration_id,)
    assert ids[18:20] == (
        "m006_07_11_nngla_road_network_construction",
        "m006_07_11_nngla_governed_spatial_publication",
    )


def test_forward_migrations_are_transaction_wrapped_verbatim_locked_schema_contracts():
    for source_name, stem in TAIL:
        source = (SCHEMAS / source_name).read_text(encoding="utf-8").rstrip("\n")
        migrated = (MIGRATIONS / f"{stem}.sql").read_text(encoding="utf-8")
        assert migrated == f"BEGIN;\n{source}\nCOMMIT;\n"


def test_existing_bundle_postgresql_contracts_remain_green_and_unmodified_in_semantics():
    checks = (
        (load_schema17h_sql, qualify_schema17h_sql),
        (load_schema17i_sql, qualify_schema17i_sql),
        (load_schema17j_sql, qualify_schema17j_sql),
        (load_schema17k_sql, qualify_schema17k_sql),
        (load_schema17l_sql, qualify_schema17l_sql),
        (load_schema17m_sql, qualify_schema17m_sql),
        (load_schema17n_sql, qualify_schema17n_sql),
        (load_schema17o_sql, qualify_schema17o_sql),
    )
    for load, qualify in checks:
        assert qualify(load()) == ()


def test_manifest_checksums_sizes_discovery_and_dependency_plan_are_clean():
    catalogue = _catalogue()
    assert MigrationDiscovery(MIGRATIONS).validate_catalogue(catalogue) is catalogue
    plan = MigrationPlanner().create_plan(catalogue)
    assert plan.migration_count >= 20
    assert tuple(item.identity.migration_id for item in plan.forward_order[10:18]) == tuple(stem for _, stem in TAIL)
    rollback_ids = tuple(item.identity.migration_id for item in plan.rollback_order)
    locked_tail = tuple(stem for _, stem in reversed(TAIL))
    start = rollback_ids.index(locked_tail[0])
    assert rollback_ids[start:start + len(locked_tail)] == locked_tail
    assert len(plan.plan_checksum) == 64


def test_remediation_manifest_exposes_complete_additive_operational_object_surface():
    tail = _catalogue().definitions[10:18]
    tables = {name for item in tail for name in item.expected_objects.tables}
    indexes = {name for item in tail for name in item.expected_objects.indexes}
    views = {name for item in tail for name in item.expected_objects.views}
    functions = {name for item in tail for name in item.expected_objects.functions}
    assert len(tables) == 32
    assert indexes == {"ix_nngla_spatial_read_projection_lookup"}
    assert views == {
        "geography.nngla_spatial_subject_read_v1",
        "geography.nngla_road_frontage_read_v1",
        "geography.nngla_geocode_name_read_v1",
    }
    assert len(functions) == 19
    assert {
        "geography.nngla_reserve_address_number",
        "geography.nngla_reserve_title_reference",
        "geography.nngla_reserve_parcel_reference",
        "geography.nngla_reserve_geometry_id",
        "geography.nngla_reserve_feature_id",
        "geography.nngla_reserve_name_id",
        "geography.nngla_claim_runtime_command",
        "geography.nngla_reverse_geocode",
    } <= functions


def test_rollbacks_are_non_cascading_and_do_not_drop_locked_base_tables():
    for _, stem in TAIL:
        rollback = (MIGRATIONS / f"{stem}_rollback.sql").read_text(encoding="utf-8").lower()
        assert " cascade" not in rollback
        assert rollback.startswith("begin;") and rollback.rstrip().endswith("commit;")
        for table in LOCKED_BASE_TABLES:
            assert f"drop table if exists geography.{table};" not in rollback


def test_address_sequence_and_spatial_read_dependencies_are_explicitly_preserved():
    addressing = (MIGRATIONS / "m006_07_11_nngla_smart_addressing_sites.sql").read_text(encoding="utf-8")
    queries = (MIGRATIONS / "m006_07_11_nngla_spatial_query_read_models.sql").read_text(encoding="utf-8")
    assert "CREATE SEQUENCE geography.nngla_address_id_sequence" in addressing
    assert "FROM geography.nngla_road_frontage" in queries
    assert "LEFT JOIN geography.nngla_geometry_version" in queries
    assert "FROM geography.nngla_geographic_name" in queries
