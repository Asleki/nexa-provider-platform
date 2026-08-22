import pytest
from registries.nngla.spatial_fabric.bundle19b.authoring import load_boundary_candidates
from registries.nngla.spatial_fabric.bundle19b.persistence import MemoryAdministrativeBoundaryRepository
def test_memory_repository_requires_completed_place_spatialization():
 r=MemoryAdministrativeBoundaryRepository(place_spatial_ready=False)
 with pytest.raises(RuntimeError): r.preflight()
def test_memory_legalization_preserves_admin_identity_and_sets_current_geometry():
 r=MemoryAdministrativeBoundaryRepository(); r.preflight(); c=load_boundary_candidates()[0]; r.qualify_geometry(c); gid=r.reserve_geometry(c); r.persist_geometry(c,gid); r.legalize(c,gid); a=r.admins[c.administrative_area_id]; assert a['boundary_status']=='LEGALIZED' and a['lifecycle']=='ACTIVE' and a['geometry_reference']==gid
def test_memory_transaction_rolls_back():
 r=MemoryAdministrativeBoundaryRepository(); c=load_boundary_candidates()[0]
 with pytest.raises(RuntimeError):
  with r.transaction():
   gid=r.reserve_geometry(c); r.persist_geometry(c,gid); r.legalize(c,gid); raise RuntimeError('boom')
 assert r.admins[c.administrative_area_id]['boundary_status']=='BOUNDARY_PENDING_LEGALIZATION' and not r.geometries
