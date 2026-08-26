import pytest
from shapely import from_wkb
from registries.nngla.spatial_realization.candidate_lifecycle.package import build_candidate_package
from registries.nngla.spatial_realization.candidate_lifecycle.qualification import CandidateStaleError,qualify_package
from ._support import nyara_and_silvermere,bound_governance


def test_nyara_then_silvermere_candidate_binds_exact_parent_candidate_and_stales_on_parent_change():
    region,fd,bd,parent,child,cfd,cbd=nyara_and_silvermere()
    region_dec=bound_governance(region,fd,bd,reviewer_actor_id="r1",approver_actor_id="a1")
    region_pkg=build_candidate_package(region,runtime_mode="production",author_actor_id="author-r",decisions=region_dec)
    child_dec=bound_governance(
        child,cfd,cbd,reviewer_actor_id="r2",approver_actor_id="a2",
        parent_candidate_id=parent.candidate_id,parent_candidate_geometry_sha256=parent.geometry_sha256,
    )
    child_pkg=build_candidate_package(child,runtime_mode="production",author_actor_id="author-c",decisions=child_dec,parent_candidate_id=parent.candidate_id,parent_candidate_geometry_sha256=parent.geometry_sha256)
    assert region_pkg.parent_administrative_area_id=="NG-ADM-000004"
    assert child_pkg.parent_candidate_id==parent.candidate_id
    assert child_pkg.parent_candidate_geometry_sha256==parent.geometry_sha256
    assert child_pkg.parent_administrative_area_id=="NG-ADM-000078"
    parent_geom=from_wkb(bytes.fromhex(parent.geometry_wkb_hex))
    q=qualify_package(
        child_pkg,child,qualifier_actor_id="qualifier",
        qualified_parent_candidate_id=parent.candidate_id,
        qualified_parent_candidate_geometry_sha256=parent.geometry_sha256,
        geometry_overrides={"NG-ADM-000078":parent_geom},
    )
    assert q.fabric_run_id==child_pkg.fabric_run_id
    assert q.status.value in {"CANDIDATE_QUALIFIED","CANDIDATE_REJECTED"}
    with pytest.raises(CandidateStaleError):
        qualify_package(
            child_pkg,child,qualifier_actor_id="qualifier",
            qualified_parent_candidate_id=parent.candidate_id,
            qualified_parent_candidate_geometry_sha256="f"*64,
            geometry_overrides={"NG-ADM-000078":parent_geom},
        )
