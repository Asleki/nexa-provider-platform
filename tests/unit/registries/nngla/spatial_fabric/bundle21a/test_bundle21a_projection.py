from registries.nngla.spatial_fabric.bundle21a.source import current_candidates
from registries.nngla.spatial_fabric.bundle21a.projection import publish

def test_operational_road_can_publish_after_live_geometry_and_separated_approval():
    road=next(c for c in current_candidates() if c.record_family=='ROAD')
    d,p,r=publish(road,geometry_id='NG-GEO-900001',submitted_by='actor:submitter',approved_by='actor:approver')
    assert d.decision=='PUBLIC' and d.map_renderable
    assert p and r and r.runtime_mode=='simulation' and r.publication_reference==p.publication_id

def test_proposed_feature_name_remains_blocked_even_with_geometry_until_name_and_geometry_publication_are_public():
    feature=next(c for c in current_candidates() if c.record_family=='GEOGRAPHIC_FEATURE')
    d,p,r=publish(feature,geometry_id=feature.geometry_reference,submitted_by='a',approved_by='b')
    assert d.decision=='BLOCKED' and p is None and r is None
    d,p,r=publish(feature,geometry_id=feature.geometry_reference,naming_status='ACTIVE_OFFICIAL',geometry_publication_status='PUBLISHED',submitted_by='a',approved_by='b')
    assert d.decision=='PUBLIC' and p and r
