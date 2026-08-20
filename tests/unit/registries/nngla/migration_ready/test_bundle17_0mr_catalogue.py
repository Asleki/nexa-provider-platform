from registries.nngla.migration_ready.catalogue import load_batch_profiles, load_domain_plan
from registries.nngla.migration_ready.contracts import DomainDisposition


def test_domain_plan_locks_migration_postures():
    plan = {row.domain_key: row for row in load_domain_plan()}
    assert plan["places-locked"].expected_count == 700
    assert plan["administrative-areas-locked"].expected_count == 192
    assert plan["roads-locked"].expected_count == 350
    assert plan["roads-candidate-only"].expected_count == 550
    assert plan["spatial-points-2411"].expected_count == 2411
    assert plan["spatial-points-2411"].disposition is DomainDisposition.BATCH_INSERT_OR_REUSE
    assert plan["roads-candidate-only"].disposition is DomainDisposition.CANDIDATE_ONLY
    assert plan["feature-pending-recognition"].disposition is DomainDisposition.PENDING_PRODUCTION_RECOGNITION
    assert plan["feature-deferred"].disposition is DomainDisposition.DEFERRED


def test_default_and_one_shot_batch_profiles_are_data_driven():
    profiles = load_batch_profiles()
    assert profiles["initial-spatial-2411"].batch_sizes == (11, 800, 800, 800)
    assert profiles["one-shot-spatial-2411"].batch_sizes == (2411,)
