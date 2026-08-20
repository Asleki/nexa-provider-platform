from registries.nngla.migration_ready import verification as module
from registries.nngla.migration_ready.contracts import (
    BaselineVerificationReport, CandidateStateReport, EmptyRegisterStatus,
)
from registries.nngla.spatial_fabric.bundle17e.canonical import canonical_by_candidate
from registries.nngla.spatial_fabric.bundle17e.geometry import geometry_by_candidate
from registries.nngla.spatial_fabric.bundle17e.persistence import MemorySpatialRepository


def test_final_verifier_requires_exact_2411_state_receipt_coverage_and_locked_guards(monkeypatch, tmp_path):
    memory = MemorySpatialRepository()
    for candidate_id, crosswalk in canonical_by_candidate().items():
        memory.persist_point(crosswalk, geometry_by_candidate()[candidate_id])

    class Repo:
        def __init__(self, connection): pass
        def snapshot(self, database_name, environment_name): return memory.snapshot()

    ready_empty = EmptyRegisterStatus(
        "addresses", "v1", "v2", "relation", True, True, 0, 0, True, True, True, ()
    )
    monkeypatch.setattr(module, "PostgreSQLSpatialRepository", Repo)
    monkeypatch.setattr(module, "_geometry_content_findings", lambda connection, geometries: ())
    monkeypatch.setattr(module, "_receipt_item_count", lambda connection: 2411)
    monkeypatch.setattr(module, "assess_empty_registers", lambda root, connection: (ready_empty,)*5)
    monkeypatch.setattr(module, "empty_registers_ready", lambda statuses: True)
    monkeypatch.setattr(
        module, "verify_immutable_baseline",
        lambda root, connection: BaselineVerificationReport(1284, 1284, (), (), True, ()),
    )
    monkeypatch.setattr(
        module, "assess_candidate_state",
        lambda root: CandidateStateReport(900, 350, 550, 37, 21, 5, 11, ()),
    )
    report = module.verify_migration_ready(
        tmp_path, object(), database_name="npp_dev", environment_name="development"
    )
    assert report.passed
    assert report.canonical_count == report.geometry_count == report.crosswalk_count == 2411
    assert report.receipt_item_count == 2411
