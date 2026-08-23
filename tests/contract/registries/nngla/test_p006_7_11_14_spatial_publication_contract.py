from registries.nngla.spatial_fabric.bundle21a.source import current_candidates
from registries.nngla.spatial_fabric.bundle21a.projection import publish

def test_p006_7_11_14_requires_durable_gate_and_keeps_runtime_explicit():
    road=next(c for c in current_candidates() if c.record_family=='ROAD')
    decision,pub,projection=publish(road,geometry_id='NG-GEO-900100',submitted_by='operator:one',approved_by='operator:two')
    assert decision.decision=='PUBLIC' and pub.publication_id.startswith('publication:nngla:')
    assert projection.projection_id.startswith('read:nngla:') and projection.runtime_mode=='simulation'
    assert projection.subject_id==road.subject_id and projection.geometry_id=='NG-GEO-900100'
