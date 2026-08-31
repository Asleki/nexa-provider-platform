import inspect
from registries.nngla.municipality_realization.postgis import PostGISMunicipalityEngine

def test_postgis_uses_exact_topology_without_tolerance_false_pass():
    source = inspect.getsource(PostGISMunicipalityEngine)
    assert "ST_Equals(u,r)" in source
    assert "ST_SymDifference(u,r)" in source
    assert "ST_CoveredBy(final_geometry,region_geometry)" in source
    assert "absolute_residue" not in source
    assert "ratio_residue" not in source
    assert "ST_SnapToGrid" not in source
    assert "ST_MakeValid" not in source

def test_realization_does_not_subtract_processed_siblings():
    source = inspect.getsource(PostGISMunicipalityEngine.realize)
    assert "city.geometry" in source
    assert "ST_Difference(" in source
    assert "ST_Difference(m1" not in source
    assert "ST_Difference(m2" not in source
    assert "ST_Difference(m3" not in source
