import json
import pytest
from dataclasses import replace

from registries.nngla.spatial_realization.candidate_lifecycle.fingerprints import canonical_json
from registries.nngla.spatial_realization.candidate_lifecycle.package import build_candidate_package
from registries.nngla.spatial_realization.candidate_lifecycle.repository import (
    CandidateCollisionError,
    MemoryCandidateLifecycleRepository,
    PostgreSQLCandidateLifecycleRepository,
)
from ._support import unresolved_preview


def test_memory_repository_replays_same_package_and_rejects_identity_collision():
    repo=MemoryCandidateLifecycleRepository()
    p=build_candidate_package(unresolved_preview(),runtime_mode="production",author_actor_id="author")
    assert repo.persist(p) is p
    assert repo.persist(p).package_sha256==p.package_sha256
    altered=replace(p,package_sha256="f"*64)
    with pytest.raises(CandidateCollisionError): repo.persist(altered)


class _Cursor:
    def __init__(self, package):
        self.package=package
        self.sql=""
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def execute(self,sql,params=()): self.sql=" ".join(sql.split())
    def fetchone(self):
        if "SELECT package_sha256,package_json FROM geography.nngla_shared_face_fabric_run" in self.sql:
            return self.package.package_sha256,json.loads(canonical_json(self.package))
        if "SELECT ST_Equals" in self.sql:
            return (True,)
        return None
    def fetchall(self):
        if "FROM geography.nngla_shared_face_fabric_input" in self.sql:
            return []  # Deliberately inconsistent with the immutable package JSON.
        return []


class _Connection:
    def __init__(self,package): self.package=package
    def cursor(self): return _Cursor(self.package)
    def commit(self): pass
    def rollback(self): pass


def test_postgresql_repository_fails_closed_when_normalized_readback_disagrees_with_package_json():
    p=build_candidate_package(unresolved_preview(),runtime_mode="production",author_actor_id="author")
    repo=PostgreSQLCandidateLifecycleRepository(_Connection(p))
    with pytest.raises(CandidateCollisionError,match="fabric input rows"):
        repo.persist(p)
