from registries.nngla.spatial_fabric.bundle19b.execution import execute_administrative_boundary_legalization
from registries.nngla.spatial_fabric.bundle19b.persistence import MemoryAdministrativeBoundaryRepository
def test_governed_execution_legalizes_all_192_atomically_and_is_idempotent():
 r=MemoryAdministrativeBoundaryRepository(); one=execute_administrative_boundary_legalization(r,'actor:submitter','actor:approver','rev:test'); assert one.status=='APPLIED' and len(r.geometries)==192 and sum(x['boundary_status']=='LEGALIZED' for x in r.admins.values())==192
 two=execute_administrative_boundary_legalization(r,'actor:submitter','actor:approver','rev:test'); assert two.status=='REUSED' and two.replayed is True and len(r.geometries)==192
