from collections import Counter
from registries.nngla.spatial_fabric.bundle20b.naming import physical_feature_names

def test_preserves_exact_twenty_governed_name_identities_without_auto_gazette():
    names=physical_feature_names(); assert len(names)==20 and len({n.name_id for n in names})==20
    assert Counter(n.name_family for n in names)==Counter({'RIVER':5,'LAKE':3,'MOUNTAIN':3,'VALLEY':3,'PLAIN':3,'PLATEAU':3})
    assert all(n.naming_status_code=='PROPOSED' and not n.official_effect for n in names)
