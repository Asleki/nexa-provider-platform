
from registries.nngla.spatial_fabric.bundle17l import effective_natural_feature_types,qualification_rules

def test_effective_natural_feature_domain_is_22_and_excludes_owned_nonphysical_domains():
    t=effective_natural_feature_types(); assert len(t)==22 and {'RIVER','LAKE','ISLAND','MOUNTAIN','OCEAN','BEACH','CLIFF'}<=set(t); assert not {'ROAD','PARCEL','MUNICIPALITY'}&set(t)
def test_rules_are_data_driven_for_every_supported_physical_type():
    r=qualification_rules(); assert len(r)==22 and len({x.feature_type_code for x in r})==22 and all(x.production_recognition_required and x.allow_retirement_without_delete for x in r)
