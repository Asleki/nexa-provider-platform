import pytest
from registries.nngla.spatial_realization.closure import build_city_closure
from registries.nngla.spatial_realization.persistence import MemorySpatialRealizationRepository


def test_memory_snapshot_is_selection_scoped_and_mixed_state_capable():
    repo=MemorySpatialRealizationRepository();a=build_city_closure('NG-PLC-000001');b=build_city_closure('NG-PLC-000086')
    snap=repo.snapshot((a,))
    assert set(snap.places)=={'NG-PLC-000001'}
    assert 'NG-PLC-000086' not in snap.places
    repo.seed_candidate(a.place_reference,associate=True)
    mixed=repo.snapshot((a,b))
    assert mixed.places['NG-PLC-000001'].spatial_assignment_status=='AUTHORITATIVE_GEOMETRY_ASSIGNED'
    assert mixed.places['NG-PLC-000086'].spatial_assignment_status=='UNMAPPED_PENDING_ASSOCIATION'


def test_transaction_rolls_back_geometry_and_allocator_state():
    repo=MemorySpatialRealizationRepository();c=build_city_closure('NG-PLC-000001').place_reference
    before=repo.allocator._next
    with pytest.raises(RuntimeError):
        with repo.transaction():
            gid=repo.reserve_geometry(c);repo.persist_geometry(c,gid);raise RuntimeError('boom')
    assert repo.allocator._next==before
    assert not repo.geometries


def test_repository_effective_date_is_validated_and_not_milestone_hard_coded():
    assert MemorySpatialRealizationRepository(effective_date='2027-01-04').effective_date=='2027-01-04'
    with pytest.raises(ValueError,match='effective_date'):
        MemorySpatialRealizationRepository(effective_date='04/01/2027')
