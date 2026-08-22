import pytest
from registries.nngla.spatial_fabric.bundle19b.contracts import AdministrativeBoundaryExecutionReceipt,GeometryRole

def receipt(**kw):
 d=dict(execution_id='nnglarun:admin-boundary:'+'a'*32,fingerprint_sha256='b'*64,database_name='novegeo',environment_name='test',repository_revision='c'*40,submitter_actor_id='actor:a',approver_actor_id='actor:b',selected_count=192,legalized_count=192,geometry_insert_count=192,status='APPLIED',replayed=False);d.update(kw);return AdministrativeBoundaryExecutionReceipt(**d)
def test_admin_boundary_role_is_distinct(): assert GeometryRole.ADMINISTRATIVE_BOUNDARY.value=='ADMINISTRATIVE_BOUNDARY'
def test_receipt_locks_exact_counts_and_actor_separation():
 assert receipt().selected_count==192
 with pytest.raises(ValueError): receipt(selected_count=191)
 with pytest.raises(ValueError): receipt(approver_actor_id='actor:a')
def test_replay_semantics():
 assert receipt(status='REUSED',replayed=True).replayed
 with pytest.raises(ValueError): receipt(status='REUSED',replayed=False)
