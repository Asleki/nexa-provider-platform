from registries.nngla.spatial_fabric.bundle19b.handlers import legalize_administrative_boundaries_handler
from registries.nngla.spatial_fabric.bundle19b.persistence import MemoryAdministrativeBoundaryRepository
def test_handler_routes_governed_legalization():
 r=MemoryAdministrativeBoundaryRepository(); out=legalize_administrative_boundaries_handler(r,{'submitter_actor_id':'actor:s','approver_actor_id':'actor:a','repository_revision':'rev'}); assert out.legalized_count==192
