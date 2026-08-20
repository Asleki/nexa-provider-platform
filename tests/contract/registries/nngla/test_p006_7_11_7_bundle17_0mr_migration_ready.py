"""P006.7.11.7 Bundle 17.0MR additive migration-ready contract."""
from pathlib import Path
import json

from registries.nngla.migration_ready.candidate_state import assess_candidate_state
from registries.nngla.migration_ready.catalogue import ROOT, load_batch_profiles, load_domain_plan
from registries.nngla.migration_ready.empty_registers import assess_empty_registers


def test_17_0mr_is_additive_and_does_not_extend_schema_migration_catalogue():
    manifest = json.loads((ROOT / "database/migrations/migration_manifest.json").read_text(encoding="utf-8"))
    assert manifest["catalogue_version"] >= 4
    assert len(manifest["migrations"]) >= 18
    assert all("migration_ready" not in row["migration_id"] for row in manifest["migrations"])


def test_migration_ready_package_is_separate_from_locked_bundle17a_through_17p():
    package = ROOT / "registries/nngla/migration_ready"
    assert package.is_dir()
    required = {
        "__init__.py", "__main__.py", "contracts.py", "catalogue.py", "batching.py",
        "reconciliation.py", "empty_registers.py", "candidate_state.py", "baseline.py",
        "preflight.py", "locking.py", "orchestrator.py", "verification.py", "cli.py",
    }
    assert required.issubset({path.name for path in package.iterdir() if path.is_file()})


def test_default_migration_profile_is_exactly_11_plus_800_plus_800_plus_800():
    profile = load_batch_profiles()["initial-spatial-2411"]
    assert profile.batch_sizes == (11, 800, 800, 800)
    assert sum(profile.batch_sizes) == 2411


def test_locked_domain_plan_never_auto_promotes_550_roads_or_pending_features():
    plan = {row.domain_key: row for row in load_domain_plan()}
    assert plan["roads-locked"].expected_count == 350
    assert plan["roads-candidate-only"].expected_count == 550
    assert plan["feature-pending-recognition"].expected_count == 5
    assert plan["feature-deferred"].expected_count == 11


def test_candidate_state_is_exactly_the_locked_source_boundary():
    assert assess_candidate_state(ROOT).passed


def test_v001_empty_history_is_preserved_and_v002_operational_successors_are_empty_ready():
    statuses = assess_empty_registers(ROOT)
    assert len(statuses) == 5
    assert all(item.ready for item in statuses)
    assert all(item.historical_path != item.operational_path for item in statuses)


def test_migration_ready_code_contains_no_local_progress_checkpoint_authority():
    package = ROOT / "registries/nngla/migration_ready"
    text = "\n".join(path.read_text(encoding="utf-8") for path in package.glob("*.py"))
    prohibited = ("progress.json", "checkpoint.json", "pickle.dump", "shelve.open")
    assert not any(token in text for token in prohibited)
