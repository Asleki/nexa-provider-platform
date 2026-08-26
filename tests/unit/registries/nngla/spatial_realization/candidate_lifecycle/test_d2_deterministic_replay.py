from registries.nngla.spatial_realization.candidate_lifecycle.package import build_candidate_package
from ._support import unresolved_preview


def test_same_unresolved_source_replays_same_run_and_package_digest():
    a=build_candidate_package(unresolved_preview(),runtime_mode="production",author_actor_id="author")
    b=build_candidate_package(unresolved_preview(),runtime_mode="production",author_actor_id="author")
    assert a.fabric_run_id==b.fabric_run_id
    assert a.package_sha256==b.package_sha256
