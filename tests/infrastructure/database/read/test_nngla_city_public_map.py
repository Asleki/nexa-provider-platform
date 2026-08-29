from infrastructure.database.read.nngla_national_map import MapBounds, NationalMapFeature, NationalMapPage
from infrastructure.database.read.nngla_city_public_map import (
    OFFICIAL_NOVEGEO_CITY_IDS,
    CityAugmentedNNGLANationalMapRepository,
    PostgreSQLCityPublicMapRepository,
)


def _city_row(subject_id="NG-ADM-000170", parent_region_id="NG-ADM-000008", geometry_type="POLYGON", geometry=None, label=None, read_version=5):
    geometry = geometry or {"type": "Polygon", "coordinates": [[[42.8,0.1],[43.3,0.1],[43.3,0.7],[42.8,0.1]]]}
    label = label or {"type": "Point", "coordinates": [43.0,0.35]}
    return (
        subject_id,
        parent_region_id,
        "City " + subject_id[-3:],
        "city-publication:nngla:" + subject_id.lower(),
        1,
        "city-geometry:nngla:" + subject_id + ":v1",
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


def test_city_repository_reads_only_new_public_view_and_emits_city_metadata():
    pool = Pool([_city_row()])
    repo = PostgreSQLCityPublicMapRepository(pool, runtime_mode="simulation")
    page = repo.list_features(
        bounds=MapBounds(42,-1,44,2),
        families=["ADMINISTRATIVE_AREA"],
        limit=50,
    )
    assert len(page.items) == 1
    item = page.items[0]
    assert item.subject_id == "NG-ADM-000170"
    assert item.family == "ADMINISTRATIVE_AREA"
    assert item.classification_code == "CITY"
    metadata = repo.metadata_for_subjects([item.subject_id])[item.subject_id]
    assert metadata.parent_region_id == "NG-ADM-000008"
    assert metadata.as_public_fields()["administrativeLevel"] == "CITY"
    sql = pool.cursor_ref.sql
    assert "FROM geography.nngla_city_public_read_v1 v" in sql
    assert "v.administrative_type_code='CITY'" in sql
    assert "v.qualification_status='QUALIFIED'" in sql
    assert "v.publication_status='PUBLISHED'" in sql


def test_city_repository_allows_zero_to_eight_incremental_publications():
    empty = PostgreSQLCityPublicMapRepository(Pool([]))
    page = empty.list_features(bounds=MapBounds(29,-8,45,8), families=["ADMINISTRATIVE_AREA"], limit=8)
    assert page.items == ()

    rows = [_city_row(subject_id=value, parent_region_id=f"NG-ADM-{index:06d}") for index, value in enumerate(OFFICIAL_NOVEGEO_CITY_IDS, 1)]
    full = PostgreSQLCityPublicMapRepository(Pool(rows))
    page = full.list_features(bounds=MapBounds(29,-8,45,8), families=["ADMINISTRATIVE_AREA"], limit=8)
    assert [item.subject_id for item in page.items] == list(OFFICIAL_NOVEGEO_CITY_IDS)


def test_city_repository_rejects_unknown_and_duplicate_city_identities():
    unknown = PostgreSQLCityPublicMapRepository(Pool([_city_row("NG-ADM-999999")]))
    try:
        unknown.list_features(bounds=MapBounds(29,-8,45,8), families=["ADMINISTRATIVE_AREA"], limit=8)
    except RuntimeError as exc:
        assert "unknown CITY identity" in str(exc)
    else:
        raise AssertionError("unknown CITY must fail closed")

    duplicate = PostgreSQLCityPublicMapRepository(Pool([_city_row(), _city_row()]))
    try:
        duplicate.list_features(bounds=MapBounds(29,-8,45,8), families=["ADMINISTRATIVE_AREA"], limit=8)
    except RuntimeError as exc:
        assert "duplicate CITY identity" in str(exc)
    else:
        raise AssertionError("duplicate CITY must fail closed")


class BaseRepo:
    runtime_mode = "simulation"
    def list_features(self, **kwargs):
        region = NationalMapFeature(
            "NG-ADM-000008","ADMINISTRATIVE_AREA","Sabaran Gulf","region-publication:nngla:8",
            "region-geometry:nngla:NG-ADM-000008:v1",1,"ADMINISTRATIVE_BOUNDARY","MULTIPOLYGON","NG-CRS-EPSG4326",
            {"type":"MultiPolygon","coordinates":[]},"SHARED_REFERENCE","NNGLA_ADMIN_TYPE","REGION",7,
        )
        stale_city = NationalMapFeature(
            "NG-ADM-000170","ADMINISTRATIVE_AREA","Stale Port Meridian","publication:nngla:stale-city",
            "NG-GEO-999999",1,"ADMINISTRATIVE_BOUNDARY","POLYGON","NG-CRS-EPSG4326",
            {"type":"Polygon","coordinates":[]},"SHARED_REFERENCE","NNGLA_ADMIN_TYPE","CITY",3,
        )
        return NationalMapPage((region, stale_city), False, None, 7)
    def get_subject(self, subject_id):
        return self.list_features().items[1] if subject_id == "NG-ADM-000170" else None


class CityRepoStub:
    runtime_mode = "simulation"
    def list_features(self, **kwargs):
        city = NationalMapFeature(
            "NG-ADM-000170","ADMINISTRATIVE_AREA","Port Meridian","city-publication:nngla:port-meridian",
            "city-geometry:nngla:NG-ADM-000170:v1",1,"ADMINISTRATIVE_BOUNDARY","POLYGON","NG-CRS-EPSG4326",
            {"type":"Polygon","coordinates":[]},"SHARED_REFERENCE","NNGLA_ADMIN_TYPE","CITY",8,
        )
        return NationalMapPage((city,), False, None, 8)
    def get_subject(self, subject_id):
        return self.list_features().items[0] if subject_id == "NG-ADM-000170" else None


class EmptyCityRepoStub:
    runtime_mode = "simulation"
    def list_features(self, **kwargs): return NationalMapPage((), False, None, 1)
    def get_subject(self, subject_id): return None


def test_city_adapter_replaces_stale_official_city_but_preserves_region():
    repo = CityAugmentedNNGLANationalMapRepository(BaseRepo(), CityRepoStub())
    page = repo.list_features(bounds=MapBounds(29,-8,45,8), families=["ADMINISTRATIVE_AREA"], limit=20)
    assert [(item.subject_id, item.display_name) for item in page.items] == [
        ("NG-ADM-000008", "Sabaran Gulf"),
        ("NG-ADM-000170", "Port Meridian"),
    ]
    assert repo.get_subject("NG-ADM-000170").geometry_id.startswith("city-geometry:nngla:")


def test_unpublished_official_city_does_not_fall_back_to_stale_generic_projection():
    repo = CityAugmentedNNGLANationalMapRepository(BaseRepo(), EmptyCityRepoStub())
    page = repo.list_features(bounds=MapBounds(29,-8,45,8), families=["ADMINISTRATIVE_AREA"], limit=20)
    assert [item.subject_id for item in page.items] == ["NG-ADM-000008"]
    assert repo.get_subject("NG-ADM-000170") is None
