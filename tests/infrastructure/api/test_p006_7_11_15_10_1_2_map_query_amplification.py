from collections import Counter
from contextlib import contextmanager
from types import SimpleNamespace

from infrastructure.database.read.nngla_city_district_public_map import (
    CityDistrictAugmentedNNGLANationalMapRepository,
    PostgreSQLCityDistrictPublicMapRepository,
)
from infrastructure.database.read.nngla_city_public_map import (
    CityAugmentedNNGLANationalMapRepository,
    OFFICIAL_NOVEGEO_CITY_IDS,
    PostgreSQLCityPublicMapRepository,
)
from infrastructure.database.read.nngla_municipality_public_map import (
    MunicipalityAugmentedNNGLANationalMapRepository,
    PostgreSQLMunicipalityPublicMapRepository,
)
from infrastructure.database.read.nngla_national_map import (
    MAP_FAMILIES,
    MapBounds,
    PostgreSQLNNGLANationalMapRepository,
)
from infrastructure.database.read.nngla_region_public_map import (
    OFFICIAL_NOVEGEO_REGION_IDS,
    PostgreSQLRegionPublicMapRepository,
    RegionAugmentedNNGLANationalMapRepository,
)
from infrastructure.database.read.nngla_town_public_map import (
    PostgreSQLTownPublicMapRepository,
    TownAugmentedNNGLANationalMapRepository,
)
from infrastructure.database.runtime.pool import PostgreSQLPool


def _polygon():
    return {"type": "Polygon", "coordinates": []}


def _point(index=0):
    return {"type": "Point", "coordinates": [35.0 + index / 100.0, index / 100.0]}


def _municipality_ids():
    return tuple(f"NG-ADM-{300000 + index:06d}" for index in range(1, 25))


def _district_ids():
    return tuple(f"NG-ADM-{400000 + index:06d}" for index in range(1, 65))


def _town_ids():
    return tuple(f"NG-PLC-{500000 + index:06d}" for index in range(1, 121))


def _region_row(subject_id, index):
    return (
        subject_id,
        f"Region {index}",
        f"publication:region:{index}",
        1,
        f"geometry:region:{index}",
        1,
        "ADMINISTRATIVE_BOUNDARY",
        "POLYGON",
        "EPSG:4326",
        _polygon(),
        "SHARED_REFERENCE",
        1,
        _point(index),
        1_000_000.0 + index,
        10_000.0 + index,
    )


def _city_row(subject_id, index):
    return (
        subject_id,
        OFFICIAL_NOVEGEO_REGION_IDS[index % len(OFFICIAL_NOVEGEO_REGION_IDS)],
        f"City {index}",
        f"publication:city:{index}",
        1,
        f"geometry:city:{index}",
        1,
        "ADMINISTRATIVE_BOUNDARY",
        "POLYGON",
        "EPSG:4326",
        _polygon(),
        "SHARED_REFERENCE",
        1,
        _point(index),
        500_000.0 + index,
        8_000.0 + index,
    )


def _municipality_row(subject_id, index):
    return (
        subject_id,
        OFFICIAL_NOVEGEO_REGION_IDS[index % len(OFFICIAL_NOVEGEO_REGION_IDS)],
        f"Municipality {index}",
        f"publication:municipality:{index}",
        1,
        f"geometry:municipality:{index}",
        1,
        "ADMINISTRATIVE_BOUNDARY",
        "POLYGON",
        "EPSG:4326",
        _polygon(),
        "SHARED_REFERENCE",
        1,
        _point(index),
        300_000.0 + index,
        6_000.0 + index,
    )


def _district_row(subject_id, index):
    return (
        subject_id,
        OFFICIAL_NOVEGEO_CITY_IDS[index % len(OFFICIAL_NOVEGEO_CITY_IDS)],
        "REGION-CODE",
        f"District {index}",
        "CITY_DISTRICT",
        f"publication:district:{index}",
        f"geometry:district:{index}",
        1,
        "POLYGON",
        "EPSG:4326",
        _polygon(),
        _point(index),
        100_000.0 + index,
        3_000.0 + index,
        f"partition:{index}",
        "COMPLETE",
    )


def _town_row(subject_id, index):
    return (
        subject_id,
        _municipality_ids()[index % 7],
        f"Town {index}",
        "TOWN",
        f"publication:town:{index}",
        f"geometry:town:{index}",
        1,
        "POLYGON",
        "EPSG:4326",
        _polygon(),
        "SHARED_REFERENCE",
        _point(index),
        50_000.0 + index,
        1_500.0 + index,
        f"qualification:town:{index}",
    )


class QueryCountingCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=()):
        normalized = " ".join(str(sql).split())
        params = tuple(params)
        self.connection.executions.append((normalized, params))

        if normalized.startswith("SET TRANSACTION READ ONLY"):
            self.rows = []
            return
        if "nngla_spatial_read_projection_v1" in normalized:
            self.connection.phases.append("base_projection")
            self.rows = []
            return
        if "nngla_region_public_read_v1" in normalized:
            self.connection.phases.append("region_records")
            self.rows = [
                _region_row(subject_id, index)
                for index, subject_id in enumerate(OFFICIAL_NOVEGEO_REGION_IDS)
            ]
            return
        if "nngla_city_public_read_v1" in normalized:
            self.connection.phases.append("city_records")
            self.rows = [
                _city_row(subject_id, index)
                for index, subject_id in enumerate(OFFICIAL_NOVEGEO_CITY_IDS)
            ]
            return
        if (
            "FROM geography.nngla_administrative_area" in normalized
            and "administrative_type_code='MUNICIPALITY'" in normalized
            and "JOIN geography.nngla_administrative_area AS parent" not in normalized
        ):
            self.connection.phases.append("municipality_governed_ids")
            self.rows = [(subject_id,) for subject_id in _municipality_ids()]
            return
        if "nngla_municipality_public_read_v2" in normalized:
            self.connection.phases.append("municipality_records")
            self.rows = [
                _municipality_row(subject_id, index)
                for index, subject_id in enumerate(_municipality_ids()[:7])
            ]
            return
        if "JOIN geography.nngla_administrative_area AS parent" in normalized:
            self.connection.phases.append("city_district_governed_ids")
            self.rows = [(subject_id,) for subject_id in _district_ids()]
            return
        if "nngla_city_district_public_read_v2" in normalized:
            self.connection.phases.append("city_district_records")
            self.rows = [
                _district_row(subject_id, index)
                for index, subject_id in enumerate(_district_ids()[:29])
            ]
            return
        if "FROM geography.nngla_place_reference" in normalized:
            self.connection.phases.append("town_governed_ids")
            self.rows = [(subject_id,) for subject_id in _town_ids()]
            return
        if "nngla_town_public_read_v2" in normalized:
            self.connection.phases.append("town_records")
            self.rows = [
                _town_row(subject_id, index)
                for index, subject_id in enumerate(_town_ids()[:22])
            ]
            return
        raise AssertionError(f"unexpected SQL: {normalized}")

    def fetchall(self):
        return list(self.rows)


class QueryCountingConnection:
    def __init__(self):
        self.executions = []
        self.phases = []

    def cursor(self):
        return QueryCountingCursor(self)


class PhysicalPool:
    def __init__(self):
        self.borrow_count = 0
        self.connection_instance = QueryCountingConnection()

    @contextmanager
    def connection(self):
        self.borrow_count += 1
        yield self.connection_instance

    def close(self):
        return None


def _settings():
    return SimpleNamespace(
        host="db",
        port=5432,
        database_name="npp",
        username="npp",
        password="test",
        ssl_mode="require",
        min_pool_size=1,
        max_pool_size=5,
        acquisition_timeout_seconds=10,
    )


def test_full_74_feature_snapshot_materializes_each_governed_layer_once():
    physical = PhysicalPool()
    pool = PostgreSQLPool(_settings(), pool_factory=lambda _settings: physical)
    pool.open()

    base = PostgreSQLNNGLANationalMapRepository(pool, runtime_mode="simulation")
    region_repository = PostgreSQLRegionPublicMapRepository(pool, runtime_mode="simulation")
    region_augmented = RegionAugmentedNNGLANationalMapRepository(base, region_repository)
    city_repository = PostgreSQLCityPublicMapRepository(pool, runtime_mode="simulation")
    city_augmented = CityAugmentedNNGLANationalMapRepository(region_augmented, city_repository)
    municipality_repository = PostgreSQLMunicipalityPublicMapRepository(pool, runtime_mode="simulation")
    municipality_augmented = MunicipalityAugmentedNNGLANationalMapRepository(
        city_augmented, municipality_repository
    )
    city_district_repository = PostgreSQLCityDistrictPublicMapRepository(
        pool, runtime_mode="simulation"
    )
    city_district_augmented = CityDistrictAugmentedNNGLANationalMapRepository(
        municipality_augmented, city_district_repository
    )
    town_repository = PostgreSQLTownPublicMapRepository(pool, runtime_mode="simulation")
    repository = TownAugmentedNNGLANationalMapRepository(
        city_district_augmented, town_repository
    )

    bounds = MapBounds(29.05, -7.7, 44.8, 7.8)
    with pool.read_session():
        page = repository.list_features(
            bounds=bounds,
            families=MAP_FAMILIES,
            limit=2000,
            after=None,
        )

        counts = Counter((item.family, item.classification_code) for item in page.items)
        assert len(page.items) == 74
        assert counts[("ADMINISTRATIVE_AREA", "REGION")] == 8
        assert counts[("ADMINISTRATIVE_AREA", "CITY")] == 8
        assert counts[("ADMINISTRATIVE_AREA", "MUNICIPALITY")] == 7
        assert counts[("ADMINISTRATIVE_AREA", "CITY_DISTRICT")] == 29
        assert counts[("PLACE", "TOWN")] == 22

        region_ids = [item.subject_id for item in page.items if item.classification_code == "REGION"]
        city_ids = [item.subject_id for item in page.items if item.classification_code == "CITY"]
        municipality_ids = [
            item.subject_id for item in page.items if item.classification_code == "MUNICIPALITY"
        ]
        district_ids = [
            item.subject_id for item in page.items if item.classification_code == "CITY_DISTRICT"
        ]
        town_ids = [item.subject_id for item in page.items if item.classification_code == "TOWN"]

        region_metadata = region_repository.metadata_for_subjects(region_ids)
        city_metadata = city_repository.metadata_for_subjects(city_ids)
        municipality_metadata = municipality_repository.metadata_for_subjects(municipality_ids)
        district_metadata = city_district_repository.metadata_for_subjects(district_ids)
        town_metadata = town_repository.metadata_for_subjects(town_ids)

        assert len(region_metadata) == 8
        assert len(city_metadata) == 8
        assert len(municipality_metadata) == 7
        assert len(district_metadata) == 29
        assert len(town_metadata) == 22
        assert all(value.label_point["type"] == "Point" for value in region_metadata.values())
        assert all(value.parent_region_id.startswith("NG-ADM-") for value in city_metadata.values())
        assert all(value.parent_region_id.startswith("NG-ADM-") for value in municipality_metadata.values())
        assert all(value.parent_city_id.startswith("NG-ADM-") for value in district_metadata.values())
        assert all(value.qualification_id.startswith("qualification:") for value in town_metadata.values())

    expected_phases = [
        "town_governed_ids",
        "city_district_governed_ids",
        "municipality_governed_ids",
        "base_projection",
        "region_records",
        "city_records",
        "municipality_records",
        "city_district_records",
        "town_records",
    ]
    assert physical.borrow_count == 1
    assert physical.connection_instance.phases == expected_phases
    assert len(physical.connection_instance.phases) == 9
    assert len(physical.connection_instance.executions) == 10
    assert physical.connection_instance.executions[0][0].startswith("SET TRANSACTION READ ONLY")
