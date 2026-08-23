from registries.nngla.spatial_fabric.bundle20b.refinement import hydro_relationships,landform_extents

def test_hydrology_relationships_preserve_physical_feature_identity():
    rels=hydro_relationships(); assert rels
    assert all(r.subject_feature_id.startswith('NG-FEAT-') and r.subject_physical_id for r in rels)
    assert any(r.relationship_type=='RECEIVES_TRIBUTARY_AT' for r in rels)
    assert any(r.relationship_type=='FLOWS_TO_COAST' for r in rels)

def test_all_twelve_landforms_gain_separate_evidence_derived_extent_candidates():
    ext=landform_extents(); assert len(ext)==11
    assert all(e.existing_geometry_id.startswith('NG-GEO-') and e.geometry_reservation_key.startswith('p006.7.11.13:landform-extent:') for e in ext)
    assert all(e.source_basis=='QUALIFIED_TERRAIN_V001_OBSERVATIONAL_CONVEX_HULL' for e in ext)
