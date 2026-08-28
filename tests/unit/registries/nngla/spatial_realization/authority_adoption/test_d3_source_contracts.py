from pathlib import Path
import inspect

import registries.nngla.spatial_realization.authority_adoption.city_qualification as qualification
import registries.nngla.spatial_realization.authority_adoption.repository as repository
import registries.nngla.spatial_realization.authority_adoption.city_publication as publication


def test_qualifier_is_select_only_and_never_allocates_geometry_identity():
    text = inspect.getsource(qualification).lower()
    assert "set transaction read only" in text
    assert "nngla_reserve_geometry_id" not in text
    for token in ("insert into", "update geography", "delete from"):
        assert token not in text


def test_qualifier_uses_parent_and_peer_read_evidence_without_authority_prerequisite():
    text = inspect.getsource(qualification)
    assert "LOCKED_FROZEN_REFERENCE" in text
    assert "CURRENT_QUALIFIED_AUTHORITY" in text
    assert "administrative_children(parent_id)" in text
    assert "REGION_LOCAL_AREAS" not in text
    assert "CANDIDATE_QUALIFIED" not in text


def test_precision_uses_reduce_precision_not_tolerance_or_snap_to_grid():
    text = inspect.getsource(qualification)
    assert "ST_ReducePrecision" in text
    assert "ST_SnapToGrid" not in text
    assert "epsilon" not in text.lower()


def test_authority_writer_is_single_city_and_binds_exact_parent_evidence():
    text = inspect.getsource(repository)
    assert "CITY administrative areas only" in text
    assert "parent_evidence_id" in text
    assert "parent_geometry_sha256" in text
    assert "nngla_reserve_geometry_id" in text
    assert "len(fabric.members)" not in text


def test_publisher_has_no_simulation_default():
    text = inspect.getsource(publication)
    assert 'runtime = "production"' in text
    assert 'runtime_mode: str = "simulation"' not in text
