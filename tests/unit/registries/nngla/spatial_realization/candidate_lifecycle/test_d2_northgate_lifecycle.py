from registries.nngla.spatial_realization.candidate_lifecycle.package import build_candidate_package
from registries.nngla.spatial_realization.candidate_lifecycle.repository import MemoryCandidateLifecycleRepository
from ._support import assigned_preview,bound_governance


def test_northgate_candidate_survives_persistence_hash_for_hash():
    preview,fd,bd=assigned_preview()
    decisions=bound_governance(preview,fd,bd)
    package=build_candidate_package(preview,runtime_mode="production",author_actor_id="author",decisions=decisions)
    repo=MemoryCandidateLifecycleRepository(); repo.persist(package)
    read=repo.get(package.fabric_run_id)
    assert read.package_sha256==package.package_sha256
    assert read.edge_graph_sha256==preview.edge_graph.graph_sha256
    assert read.face_set_sha256==preview.face_set.face_set_sha256
    assert all(d.fabric_run_id==package.fabric_run_id and d.scope_fingerprint==package.scope_fingerprint for d in package.decisions)
