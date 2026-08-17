from registries.nngla.spatial_fabric.bundle17o.contracts import GeocodeMatch,GeocodeStatus
from registries.nngla.spatial_fabric.bundle17o.geocoding import MemoryGeocoder,geocoding_rules
def match(i,scope,visibility="PUBLIC"):
    return GeocodeMatch(i,f"NG-NAM-{i[-1]:0>6}","PLACE","Café Ridge",scope,visibility,None,None)
def test_geocoder_reuses_unicode_normalization_and_preserves_ambiguity():
    g=MemoryGeocoder((match("p1","scope:a"),match("p2","scope:b")))
    result=g.geocode("  CAFE\u0301   RIDGE ")
    assert result.status is GeocodeStatus.MULTIPLE_MATCHES and len(result.matches)==2
    assert g.geocode("café ridge",scope_reference="scope:a").status is GeocodeStatus.UNIQUE_MATCH
    assert {"NFKC","CASEFOLD","COLLAPSE_WHITESPACE"}<={r["normalization_step"] for r in geocoding_rules()}
