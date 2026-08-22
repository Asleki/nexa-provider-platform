from registries.nngla.spatial_fabric.bundle19b.topology import load_topology_policy,load_topology_relationships,hierarchy_counts
def test_topology_policy_distinguishes_territorial_and_overlay_semantics():
 p=load_topology_policy(); assert p['REGION']['gap_policy']=='PROHIBITED'; assert p['CITY_DISTRICT']['sibling_positive_area_overlap']=='PROHIBITED'; assert p['INDUSTRIAL_ZONE']['partition_mode']=='NON_EXHAUSTIVE_OVERLAY'; assert p['INDUSTRIAL_ZONE']['gap_policy']=='NOT_APPLICABLE'
def test_every_admin_identity_has_qualified_parent_topology(): assert len(load_topology_relationships())==192
def test_hierarchy_counts_are_locked():
 c=hierarchy_counts(); assert c['REGION']==8 and c['CITY']==8 and c['MUNICIPALITY']==24 and c['CITY_DISTRICT']==64 and c['TOWNSHIP']==72 and c['INDUSTRIAL_ZONE']==16
