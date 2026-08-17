from registries.nngla.spatial_fabric.bundle17j import geometry_namespace_baseline,occupied_geometry_ids

def test_geometry_namespace_includes_17e_allocations_without_collision():
 b=geometry_namespace_baseline(); assert len(occupied_geometry_ids())==2432; assert b['max_geometry_id']=='NG-GEO-002432'; assert b['next_candidate_id']=='NG-GEO-002433'; assert b['collision_free']
