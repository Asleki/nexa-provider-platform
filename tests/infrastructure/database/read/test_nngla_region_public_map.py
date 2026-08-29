from infrastructure.database.read.nngla_national_map import MapBounds, NationalMapFeature, NationalMapPage
from infrastructure.database.read.nngla_region_public_map import (
    OFFICIAL_NOVEGEO_REGION_IDS,
    PostgreSQLRegionPublicMapRepository,
    RegionAugmentedNNGLANationalMapRepository,
)


def _region_row(subject_id="NG-ADM-000001", geometry_type="POLYGON", geometry=None, label=None, read_version=4):
    geometry = geometry or {"type": "Polygon", "coordinates": [[[30,-1],[31,-1],[31,0],[30,-1]]]}
    label = label or {"type": "Point", "coordinates": [30.5,-0.5]}
    return (
        subject_id,
        "Region " + subject_id[-1],
        "publication:nngla:" + subject_id.lower(),
        1,
        "NG-GEO-123456",
        1,
        "ADMINISTRATIVE_BOUNDARY",
        geometry_type,
        "NG-CRS-EPSG4326",
        geometry,
        "SHARED_REFERENCE",
        read_version,
        label,
        12345.5,
        456.75,
    )


class Cursor:
    def __init__(self, rows):
        self.rows = rows
        self.sql = None
        self.params = None
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, params):
        self.sql = sql
        self.params = params
    def fetchall(self): return list(self.rows)


class Connection:
    def __init__(self, cursor): self._cursor = cursor
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def cursor(self): return self._cursor


class Pool:
    def __init__(self, rows): self.cursor_ref = Cursor(rows)
    def connection(self, read_only=False):
        assert read_only is True
        return Connection(self.cursor_ref)


def test_region_repository_reads_public_view_as_allowlist_and_emits_governed_map_feature():
    pool = Pool([_region_row()])
    repo = PostgreSQLRegionPublicMapRepository(pool, runtime_mode="simulation")
    page = repo.list_features(
        bounds=MapBounds(29,-2,32,1),
        families=["ADMINISTRATIVE_AREA"],
        limit=50,
    )
    assert len(page.items) == 1
    item = page.items[0]
    assert item.subject_id == "NG-ADM-000001"
    assert item.family == "ADMINISTRATIVE_AREA"
    assert item.classification_scheme == "NNGLA_ADMIN_TYPE"
    assert item.classification_code == "REGION"
    assert item.geometry["type"] == "Polygon"
    sql = pool.cursor_ref.sql
    assert "geography.nngla_region_public_read_v1" in sql
    assert "FROM geography.nngla_region_public_read_v1 v" in sql
    assert "v.administrative_type_code='REGION'" in sql
    assert "v.qualification_status='QUALIFIED'" in sql
    assert "v.publication_status='PUBLISHED'" in sql
    assert "ST_Intersects(v.geometry" in sql
    assert "jsonb_build_object" in sql


def test_region_repository_supports_polygon_and_multipolygon_and_public_metadata():
    multipolygon = {"type":"MultiPolygon","coordinates":[[[[30,0],[31,0],[31,1],[30,0]]],[[[32,0],[33,0],[33,1],[32,0]]]]}
    rows = [
        _region_row("NG-ADM-000001"),
        _region_row("NG-ADM-000002", "MULTIPOLYGON", multipolygon, {"type":"Point","coordinates":[32.5,0.5]}, 5),
    ]
    repo = PostgreSQLRegionPublicMapRepository(Pool(rows), runtime_mode="production")
    page = repo.list_features(bounds=MapBounds(29,-2,34,2), families=["ADMINISTRATIVE_AREA"], limit=8)
    assert [item.geometry_type for item in page.items] == ["POLYGON", "MULTIPOLYGON"]
    metadata = repo.metadata_for_subjects(["NG-ADM-000001", "NG-ADM-000002"])
    assert metadata["NG-ADM-000002"].label_point["type"] == "Point"
    public = metadata["NG-ADM-000002"].as_public_fields()
    assert public["administrativeLevel"] == "REGION"
    assert public["labelAnchorKind"] == "DERIVED_PRESENTATION"
    assert public["labelPointAlgorithmId"] == "algorithm:nngla:region-label-point-on-surface:epsg4326"
    assert public["areaM2"] > 0 and public["perimeterM"] > 0


def test_region_repository_rejects_unknown_region_identity_from_public_view():
    repo = PostgreSQLRegionPublicMapRepository(Pool([_region_row("NG-ADM-999999")]))
    try:
        repo.list_features(bounds=MapBounds(29,-2,32,1), families=["ADMINISTRATIVE_AREA"], limit=8)
    except RuntimeError as exc:
        assert "unknown REGION identity" in str(exc)
    else:
        raise AssertionError("unknown region must fail closed")


class BaseRepo:
    runtime_mode = "simulation"
    def list_features(self, **kwargs):
        city = NationalMapFeature(
            "NG-ADM-000009","ADMINISTRATIVE_AREA","City","publication:nngla:city",
            "NG-GEO-654321",1,"ADMINISTRATIVE_BOUNDARY","POLYGON","NG-CRS-EPSG4326",
            {"type":"Polygon","coordinates":[[[31,0],[32,0],[32,1],[31,0]]]},
            "SHARED_REFERENCE","NNGLA_ADMIN_TYPE","CITY",3,
        )
        return NationalMapPage((city,), False, None, 3)
    def get_subject(self, subject_id): return None


class RegionRepoStub:
    runtime_mode = "simulation"
    def list_features(self, **kwargs):
        region = NationalMapFeature(
            "NG-ADM-000001","ADMINISTRATIVE_AREA","Region","publication:nngla:region",
            "NG-GEO-123456",1,"ADMINISTRATIVE_BOUNDARY","POLYGON","NG-CRS-EPSG4326",
            {"type":"Polygon","coordinates":[[[30,0],[31,0],[31,1],[30,0]]]},
            "SHARED_REFERENCE","NNGLA_ADMIN_TYPE","REGION",7,
        )
        return NationalMapPage((region,), False, None, 7)
    def get_subject(self, subject_id): return None


def test_augmented_repository_merges_region_before_existing_admin_features_without_new_family():
    repo = RegionAugmentedNNGLANationalMapRepository(BaseRepo(), RegionRepoStub())
    page = repo.list_features(bounds=MapBounds(29,-2,34,2), families=["ADMINISTRATIVE_AREA"], limit=10)
    assert [(item.subject_id,item.classification_code) for item in page.items] == [
        ("NG-ADM-000001","REGION"),
        ("NG-ADM-000009","CITY"),
    ]
    assert all(item.family == "ADMINISTRATIVE_AREA" for item in page.items)
    assert page.read_model_version == 7


def test_official_region_identity_contract_is_exactly_eight():
    assert OFFICIAL_NOVEGEO_REGION_IDS == tuple(f"NG-ADM-{i:06d}" for i in range(1,9))

class StaleRegionBaseRepo:
    runtime_mode = "simulation"
    def list_features(self, **kwargs):
        stale = NationalMapFeature(
            "NG-ADM-000001","ADMINISTRATIVE_AREA","Stale Region","publication:nngla:stale",
            "NG-GEO-999998",1,"ADMINISTRATIVE_BOUNDARY","POLYGON","NG-CRS-EPSG4326",
            {"type":"Polygon","coordinates":[[[30,0],[31,0],[31,1],[30,0]]]},
            "SHARED_REFERENCE","NNGLA_ADMIN_TYPE","REGION",2,
        )
        city = NationalMapFeature(
            "NG-ADM-000009","ADMINISTRATIVE_AREA","City","publication:nngla:city",
            "NG-GEO-999999",1,"ADMINISTRATIVE_BOUNDARY","POLYGON","NG-CRS-EPSG4326",
            {"type":"Polygon","coordinates":[[[31,0],[32,0],[32,1],[31,0]]]},
            "SHARED_REFERENCE","NNGLA_ADMIN_TYPE","CITY",2,
        )
        return NationalMapPage((stale, city), False, None, 2)
    def get_subject(self, subject_id):
        return self.list_features().items[0] if subject_id == "NG-ADM-000001" else None


class EmptyRegionRepoStub:
    runtime_mode = "simulation"
    def list_features(self, **kwargs): return NationalMapPage((), False, None, 1)
    def get_subject(self, subject_id): return None


def test_augmented_repository_fails_closed_instead_of_leaking_stale_region_projection():
    repo = RegionAugmentedNNGLANationalMapRepository(StaleRegionBaseRepo(), EmptyRegionRepoStub())
    page = repo.list_features(bounds=MapBounds(29,-2,34,2), families=["ADMINISTRATIVE_AREA"], limit=10)
    assert [item.subject_id for item in page.items] == ["NG-ADM-000009"]
    assert repo.get_subject("NG-ADM-000001") is None
