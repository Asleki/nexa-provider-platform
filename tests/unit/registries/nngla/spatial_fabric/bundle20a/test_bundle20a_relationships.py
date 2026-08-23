from registries.nngla.spatial_fabric.bundle20a.relationships import derive_relationships

def test_every_road_has_place_and_region_relationships():
    rels=derive_relationships(); by={}
    for r in rels: by.setdefault(r.road_id,set()).add(r.relationship_type)
    assert len(by)==350
    assert all({'STARTS_AT_PLACE','ENDS_AT_PLACE','WITHIN_ADMIN_REGION'}<=types for types in by.values())
    assert all(r.evidence_basis!='' for r in rels)
