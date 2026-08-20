"""Integration-level proof that committed batches survive a later batch failure."""
import pytest

from registries.nngla.migration_ready.orchestrator import (
    build_spatial_preview, confirmation_token, execute_spatial,
)
from registries.nngla.spatial_fabric.bundle17e.persistence import MemorySpatialRepository


class FailureAfterFirstCommittedBatch(MemorySpatialRepository):
    def __init__(self):
        super().__init__(database_name="integration", environment_name="test")
        self.calls = 0
        self.failure_enabled = True
    def persist_point(self, crosswalk, geometry):
        self.calls += 1
        if self.failure_enabled and self.calls == 25:
            raise ConnectionError("simulated transport loss")
        return super().persist_point(crosswalk, geometry)


def _run(repo, preview):
    return execute_spatial(
        repo,
        database_name="integration",
        environment_name="test",
        repository_revision="integration-rev",
        approved_fingerprint=preview.fingerprint,
        confirmation=confirmation_token("integration", preview.fingerprint),
        submitter_actor_id="actor:submitter",
        approver_actor_id="actor:approver",
    )


def test_resume_uses_committed_target_not_process_memory_checkpoint():
    repo = FailureAfterFirstCommittedBatch()
    preview = build_spatial_preview(
        repo, database_name="integration", environment_name="test", repository_revision="integration-rev"
    )
    with pytest.raises(ConnectionError):
        _run(repo, preview)
    assert len(repo.crosswalks) == 11
    assert len(repo.receipts) == 1

    repo.failure_enabled = False
    resume_preview = build_spatial_preview(
        repo, database_name="integration", environment_name="test", repository_revision="integration-rev"
    )
    assert resume_preview.reuse_count == 11
    assert resume_preview.insert_count == 2400
    results = _run(repo, resume_preview)
    assert results[0].status == "REUSED"
    assert sum(row.inserted_count for row in results) == 2400
    assert len(repo.crosswalks) == 2411
    assert len(repo.geometry_by_subject) == 2411
