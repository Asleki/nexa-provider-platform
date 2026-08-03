from dataclasses import replace
from pathlib import Path

import pytest

from database.migration_control.errors import MigrationCycleError, MigrationDependencyError, MigrationOrderError
from database.migration_control.manifest import MigrationManifestLoader
from database.migration_control.planning import MigrationPlanner
from database.migration_control.contracts import MigrationCatalogue


ROOT = Path(__file__).parents[4]
MANIFEST = ROOT / "database/migrations/migration_manifest.json"


def load_catalogue():
    return MigrationManifestLoader().load(MANIFEST)


def test_real_chain_has_exact_forward_and_reverse_rollback_order():
    plan = MigrationPlanner().create_plan(load_catalogue())
    assert [item.identity.migration_id for item in plan.forward_order] == [
        "m009_10_04_name_catalogue",
        "m009_12_06_name_authority",
        "m009_12_09_name_authority_generation",
        "m009_12_12_name_authority_application",
        "m009_13_10_reference_registry_authoring",
    ]
    assert [item.identity.migration_id for item in plan.rollback_order] == [
        "m009_13_10_reference_registry_authoring",
        "m009_12_12_name_authority_application",
        "m009_12_09_name_authority_generation",
        "m009_12_06_name_authority",
        "m009_10_04_name_catalogue",
    ]
    assert plan.migration_count == 5
    assert len(plan.plan_checksum) == 64


def test_same_catalogue_produces_stable_plan_checksum():
    planner = MigrationPlanner()
    assert planner.create_plan(load_catalogue()).plan_checksum == planner.create_plan(load_catalogue()).plan_checksum


def test_missing_dependency_blocks_plan():
    catalogue = load_catalogue()
    definitions = list(catalogue.definitions)
    definitions[1] = replace(definitions[1], depends_on=("missing_migration",))
    broken = replace(catalogue, definitions=tuple(definitions))
    with pytest.raises(MigrationDependencyError):
        MigrationPlanner().create_plan(broken)


def test_cycle_blocks_plan():
    catalogue = load_catalogue()
    definitions = list(catalogue.definitions)
    definitions[0] = replace(definitions[0], depends_on=(definitions[-1].identity.migration_id,))
    broken = replace(catalogue, definitions=tuple(definitions))
    with pytest.raises(MigrationCycleError):
        MigrationPlanner().create_plan(broken)


def test_sequence_conflicting_with_dependency_order_is_rejected():
    catalogue = load_catalogue()
    definitions = list(catalogue.definitions)
    definitions[0] = replace(definitions[0], identity=replace(definitions[0].identity, sequence_number=5))
    definitions[-1] = replace(definitions[-1], identity=replace(definitions[-1].identity, sequence_number=1))
    broken = replace(catalogue, definitions=tuple(definitions))
    with pytest.raises(MigrationOrderError):
        MigrationPlanner().create_plan(broken)
