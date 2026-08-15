from pathlib import Path
from database.migration_control.discovery import MigrationDiscovery
from database.migration_control.manifest import MigrationManifestLoader
from database.migration_control.planning import MigrationPlanner
from registries.nngla.migration_architecture.plans import PLAN_CATALOGUE
from registries.nngla.migration_architecture.execution import confirmation_token

ROOT=Path(__file__).resolve().parents[4]
MIG=ROOT/"database"/"migrations"

def test_bundle16c_additive_schema_chain_installs_all_26_nngla_domain_tables_plus_execution_infrastructure():
    catalogue=MigrationManifestLoader().load(MIG/"migration_manifest.json")
    MigrationDiscovery(MIG).validate_catalogue(catalogue)
    plan=MigrationPlanner().create_plan(catalogue)
    ids=[x.identity.migration_id for x in plan.forward_order]
    assert len(ids)==10
    assert ids[-4:]==[
        "m006_07_11_nngla_execution_foundation","m006_07_11_nngla_identity_places_runtime",
        "m006_07_11_nngla_geometry_roads_runtime","m006_07_11_nngla_cadastre_runtime",
    ]
    tables={t for d in catalogue.definitions[-4:] for t in d.expected_objects.tables}
    assert "geography.nngla_place_reference" in tables
    assert "geography.nngla_administrative_area" in tables
    assert "geography.nngla_execution_receipt" in tables
    assert "geography.nngla_execution_item" in tables
    assert len(tables)==28

def test_bundle16c_runtime_schema_adds_true_canonical_place_and_admin_ids_without_rewriting_locked_contract_files():
    sql=(MIG/"m006_07_11_nngla_identity_places_runtime.sql").read_text().lower()
    assert "place_id text primary key" in sql
    assert "source_place_code text not null unique" in sql
    assert "administrative_area_id text primary key" in sql
    assert "administrative_candidate_id text not null unique" in sql
    old=(ROOT/"database/schemas/nngla_geographic_identity_places.sql").read_text()
    assert "source_place_code text PRIMARY KEY" in old
    assert "administrative_candidate_id text PRIMARY KEY" in old

def test_bundle16c_terminal_plans_remain_configuration_catalogue_not_one_sql_migration_per_batch():
    assert {"roads","places:city","places:town","places:municipality","places:village","names:hill","names:valley"} <= set(PLAN_CATALOGUE)
    migration_names={p.name for p in MIG.glob("*.sql")}
    assert not any("road_batch" in name or "town_batch" in name or "hill_batch" in name for name in migration_names)
    assert confirmation_token("roads","npp_dev","a"*64)=="RUN NNGLA PLAN roads npp_dev aaaaaaaaaaaa"

def test_bundle16c_canonicalization_does_not_auto_publish():
    text=(ROOT/"registries/nngla/migration_architecture/execution.py").read_text()
    assert "publish(" not in text
    migration=(MIG/"m006_07_11_nngla_execution_foundation.sql").read_text()
    assert "publication_ready boolean" in migration
