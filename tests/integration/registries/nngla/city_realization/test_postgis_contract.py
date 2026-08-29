from registries.nngla.city_realization.contracts import CitySourceEvidence, ParentRegionAuthority
from registries.nngla.city_realization.postgis import PostGISCityRealizationEngine


class Cursor:
    def __init__(self, rows): self.rows = list(rows); self.sql = ""; self.params = ()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, params=()): self.sql = sql; self.params = params
    def fetchone(self): return self.rows[0] if self.rows else None
    def fetchall(self): return list(self.rows)


class Connection:
    def __init__(self, cursor): self.cursor_ref = cursor
    def cursor(self): return self.cursor_ref


def test_realization_contract_uses_exact_parent_and_single_intersection_normalization():
    row = (
        False, True, True, "POLYGON", True, True, "POLYGON", True,
        100.0, 2.0, 98.0, 40.0,
        {"type":"Polygon","coordinates":[[[0,0],[1,0],[0,1],[0,0]]]},
        {"type":"Point","coordinates":[0.2,0.2]}, True,
    )
    cursor = Cursor([row])
    engine = PostGISCityRealizationEngine(Connection(cursor))
    source = CitySourceEvidence(
        "NG-ADM-000170","Port Meridian","NGR-08","NGC-08","candidate-8",
        "dataset:novegeo:administrative-boundaries","1","source.geojson",
        "a"*64,"b"*64,"POLYGON",
        {"type":"Polygon","coordinates":[[[0,0],[1,0],[0,1],[0,0]]]},
    )
    parent = ParentRegionAuthority("NG-ADM-000008","Sabaran Gulf","NGR-08","region-geometry:nngla:NG-ADM-000008:v1","c"*64)
    result = engine.realize(source, parent)
    assert result.method.value == "PARENT_CONTAINED_NORMALIZATION"
    assert result.area_removed_m2 == 2.0
    assert "ST_Intersection(source.geometry,parent.geometry)" in cursor.sql
    assert cursor.sql.count("ST_Intersection") == 1
    assert "ST_SnapToGrid" not in cursor.sql
    assert "nngla_city_feature_qualification" not in cursor.sql
    assert cursor.params[:3] == (parent.region_geometry_id, parent.region_id, parent.geometry_sha256)
