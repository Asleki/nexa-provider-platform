from registries.nngla.spatial_fabric.bundle20b.naming import physical_feature_names
from registries.nngla.spatial_fabric.bundle20b.refinement import hydro_relationships,landform_extents

def test_p006_7_11_13_identity_geometry_name_separation():
    names=physical_feature_names(); ext=landform_extents(); rels=hydro_relationships()
    assert len(names)==20 and len(ext)==11 and rels
    assert all(n.feature_id!=n.name_id and n.physical_subject_id!=n.name_id for n in names)
    assert all(e.feature_id!=e.existing_geometry_id for e in ext)
    assert all(not n.official_effect for n in names)
