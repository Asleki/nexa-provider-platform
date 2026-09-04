from contextlib import contextmanager
from types import SimpleNamespace

from infrastructure.database.read.nngla_city_public_map import (
    OFFICIAL_NOVEGEO_CITY_IDS,
    PostgreSQLCityPublicMapRepository,
)
from infrastructure.database.read.nngla_national_map import MapBounds
from infrastructure.database.read.nngla_region_public_map import (
    OFFICIAL_NOVEGEO_REGION_IDS,
    PostgreSQLRegionPublicMapRepository,
)
from infrastructure.database.runtime.pool import PostgreSQLPool


def _polygon():
    return {"type": "Polygon", "coordinates": []}


def _point():
    return {"type": "Point", "coordinates": [35.0, 0.0]}


def _region_row(subject_id):
    return (
        subject_id,
        f"Region {subject_id}",
        f"publication:{subject_id}",
        1,
        f"geometry:{subject_id}",
        1,
        "ADMINISTRATIVE_BOUNDARY",
        "POLYGON",
        "EPSG:4326",
        _polygon(),
        "SHARED_REFERENCE",
        1,
        _point(),
        1000.0,
        200.0,
    )


def _city_row(subject_id, parent_region_id):
    return (
        subject_id,
        parent_region_id,
        f"City {subject_id}",
        f"publication:{subject_id}",
        1,
        f"geometry:{subject_id}",
        1,
        "ADMINISTRATIVE_BOUNDARY",
        "POLYGON",
        "EPSG:4326",
        _polygon(),
        "SHARED_REFERENCE",
        1,
        _point(),
        1000.0,
        200.0,
    )


class DispatcherCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=()):
        normalized = " ".join(str(sql).split())
        self.connection.executions.append((normalized, tuple(params)))
        if normalized.startswith("SET TRANSACTION READ ONLY"):
            self.rows = []
        elif "geography.nngla_region_public_read_v1" in normalized:
            ids = OFFICIAL_NOVEGEO_REGION_IDS[:1] if params else OFFICIAL_NOVEGEO_REGION_IDS[:2]
            self.rows = [_region_row(subject_id) for subject_id in ids]
        elif "geography.nngla_city_public_read_v1" in normalized:
            ids = OFFICIAL_NOVEGEO_CITY_IDS[:1] if params else OFFICIAL_NOVEGEO_CITY_IDS[:2]
            self.rows = [
                _city_row(subject_id, OFFICIAL_NOVEGEO_REGION_IDS[index % 2])
                for index, subject_id in enumerate(ids)
            ]
        else:
            raise AssertionError(f"unexpected SQL: {normalized}")

    def fetchall(self):
        return list(self.rows)


class DispatcherConnection:
    def __init__(self):
        self.executions = []

    def cursor(self):
        return DispatcherCursor(self)


class PhysicalPool:
    def __init__(self):
        self.borrow_count = 0
        self.connection_instance = DispatcherConnection()

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


def _pool():
    physical = PhysicalPool()
    pool = PostgreSQLPool(_settings(), pool_factory=lambda _settings: physical)
    pool.open()
    return pool, physical


def _view_query_count(physical, view):
    return sum(view in sql for sql, _params in physical.connection_instance.executions)


def test_region_metadata_reuses_successful_bounded_records_and_falls_back_when_incomplete():
    pool, physical = _pool()
    repository = PostgreSQLRegionPublicMapRepository(pool, runtime_mode="simulation")
    bounds = MapBounds(29.0, -8.0, 45.0, 8.0)
    first_id, second_id = OFFICIAL_NOVEGEO_REGION_IDS[:2]

    with pool.read_session():
        page = repository.list_features(bounds=bounds, limit=2000)
        assert [item.subject_id for item in page.items] == [first_id]

        cached = repository.metadata_for_subjects([first_id])
        assert set(cached) == {first_id}
        assert _view_query_count(physical, "nngla_region_public_read_v1") == 1

        complete = repository.metadata_for_subjects([first_id, second_id])
        assert set(complete) == {first_id, second_id}
        assert _view_query_count(physical, "nngla_region_public_read_v1") == 2

        again = repository.metadata_for_subjects([first_id, second_id])
        assert set(again) == {first_id, second_id}
        assert _view_query_count(physical, "nngla_region_public_read_v1") == 2

    assert physical.borrow_count == 1


def test_city_metadata_reuses_successful_bounded_records_and_falls_back_when_incomplete():
    pool, physical = _pool()
    repository = PostgreSQLCityPublicMapRepository(pool, runtime_mode="simulation")
    bounds = MapBounds(29.0, -8.0, 45.0, 8.0)
    first_id, second_id = OFFICIAL_NOVEGEO_CITY_IDS[:2]

    with pool.read_session():
        page = repository.list_features(bounds=bounds, limit=2000)
        assert [item.subject_id for item in page.items] == [first_id]

        cached = repository.metadata_for_subjects([first_id])
        assert set(cached) == {first_id}
        assert _view_query_count(physical, "nngla_city_public_read_v1") == 1

        complete = repository.metadata_for_subjects([first_id, second_id])
        assert set(complete) == {first_id, second_id}
        assert _view_query_count(physical, "nngla_city_public_read_v1") == 2

        again = repository.metadata_for_subjects([first_id, second_id])
        assert set(again) == {first_id, second_id}
        assert _view_query_count(physical, "nngla_city_public_read_v1") == 2

    assert physical.borrow_count == 1

from infrastructure.database.read.nngla_city_district_public_map import (
    PostgreSQLCityDistrictPublicMapRepository,
)
from infrastructure.database.read.nngla_municipality_public_map import (
    EXPECTED_MUNICIPALITY_COUNT,
    PostgreSQLMunicipalityPublicMapRepository,
)
from infrastructure.database.read.nngla_town_public_map import (
    PostgreSQLTownPublicMapRepository,
)
from infrastructure.database.read.nngla_national_map import NNGLAMapReadAuthorityError


def _municipality_ids():
    return tuple(f"NG-ADM-{100000 + index:06d}" for index in range(1, EXPECTED_MUNICIPALITY_COUNT + 1))


def _municipality_row(subject_id, parent_region_id="NG-ADM-000001"):
    return (
        subject_id,
        parent_region_id,
        f"Municipality {subject_id}",
        f"publication:{subject_id}",
        1,
        f"geometry:{subject_id}",
        1,
        "ADMINISTRATIVE_BOUNDARY",
        "POLYGON",
        "EPSG:4326",
        _polygon(),
        "SHARED_REFERENCE",
        1,
        _point(),
        1000.0,
        200.0,
    )


def _district_ids():
    return ("NG-ADM-200001", "NG-ADM-200002")


def _district_row(subject_id, parent_city_id="NG-ADM-000009"):
    return (
        subject_id,
        parent_city_id,
        "ORIVANE",
        f"District {subject_id}",
        "CITY_DISTRICT",
        f"publication:{subject_id}",
        f"geometry:{subject_id}",
        1,
        "POLYGON",
        "EPSG:4326",
        _polygon(),
        _point(),
        1000.0,
        200.0,
        f"partition:{subject_id}",
        "COMPLETE",
    )


def _town_ids():
    return ("NG-PLC-300001", "NG-PLC-300002")


def _town_row(subject_id, parent_place_id="NG-ADM-100001"):
    return (
        subject_id,
        parent_place_id,
        f"Town {subject_id}",
        "TOWN",
        f"publication:{subject_id}",
        f"footprint:{subject_id}",
        1,
        "POLYGON",
        "EPSG:4326",
        _polygon(),
        "SHARED_REFERENCE",
        _point(),
        1000.0,
        200.0,
        f"qualification:{subject_id}",
    )


class LayerDispatcherCursor:
    def __init__(self, connection):
        self.connection = connection
        self.rows = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql, params=()):
        normalized = " ".join(str(sql).split())
        self.connection.executions.append((normalized, tuple(params)))
        if normalized.startswith("SET TRANSACTION READ ONLY"):
            self.rows = []
            return

        if "FROM geography.nngla_administrative_area" in normalized and "administrative_type_code='MUNICIPALITY'" in normalized:
            self.connection.municipality_identity_calls += 1
            if self.connection.invalid_municipality_once and self.connection.municipality_identity_calls == 1:
                ids = _municipality_ids()[:-1]
            else:
                ids = _municipality_ids()
            self.rows = [(subject_id,) for subject_id in ids]
            return

        if "geography.nngla_municipality_public_read_v2" in normalized:
            ids = _municipality_ids()[:1] if params else _municipality_ids()[:2]
            self.rows = [_municipality_row(subject_id) for subject_id in ids]
            return

        if "JOIN geography.nngla_administrative_area AS parent" in normalized and "parent.administrative_type_code='CITY'" in normalized:
            self.rows = [(subject_id,) for subject_id in _district_ids()]
            return

        if "geography.nngla_city_district_public_read_v2" in normalized:
            ids = _district_ids()[:1] if params else _district_ids()
            self.rows = [_district_row(subject_id) for subject_id in ids]
            return

        if "FROM geography.nngla_place_reference" in normalized and "upper(place_type_code)='TOWN'" in normalized:
            self.rows = [(subject_id,) for subject_id in _town_ids()]
            return

        if "geography.nngla_town_public_read_v2" in normalized:
            ids = _town_ids()[:1] if params else _town_ids()
            self.rows = [_town_row(subject_id) for subject_id in ids]
            return

        raise AssertionError(f"unexpected SQL: {normalized}")

    def fetchall(self):
        return list(self.rows)


class LayerDispatcherConnection:
    def __init__(self, *, invalid_municipality_once=False):
        self.executions = []
        self.invalid_municipality_once = invalid_municipality_once
        self.municipality_identity_calls = 0

    def cursor(self):
        return LayerDispatcherCursor(self)


class LayerPhysicalPool:
    def __init__(self, *, invalid_municipality_once=False):
        self.borrow_count = 0
        self.connection_instance = LayerDispatcherConnection(
            invalid_municipality_once=invalid_municipality_once
        )

    @contextmanager
    def connection(self):
        self.borrow_count += 1
        yield self.connection_instance

    def close(self):
        return None


def _layer_pool(*, invalid_municipality_once=False):
    physical = LayerPhysicalPool(invalid_municipality_once=invalid_municipality_once)
    pool = PostgreSQLPool(_settings(), pool_factory=lambda _settings: physical)
    pool.open()
    return pool, physical


def _sql_count(physical, marker):
    return sum(marker in sql for sql, _params in physical.connection_instance.executions)


def test_municipality_governed_ids_and_records_are_reused_with_complete_set_fallback():
    pool, physical = _layer_pool()
    repository = PostgreSQLMunicipalityPublicMapRepository(pool, runtime_mode="simulation")
    bounds = MapBounds(29.0, -8.0, 45.0, 8.0)
    first_id, second_id = _municipality_ids()[:2]

    with pool.read_session():
        assert len(repository.governed_ids()) == EXPECTED_MUNICIPALITY_COUNT
        assert len(repository.governed_ids()) == EXPECTED_MUNICIPALITY_COUNT
        assert physical.connection_instance.municipality_identity_calls == 1

        page = repository.list_features(bounds=bounds, limit=2000)
        assert [item.subject_id for item in page.items] == [first_id]
        assert _sql_count(physical, "nngla_municipality_public_read_v2") == 1
        assert physical.connection_instance.municipality_identity_calls == 1

        cached = repository.metadata_for_subjects([first_id])
        assert set(cached) == {first_id}
        assert _sql_count(physical, "nngla_municipality_public_read_v2") == 1

        complete = repository.metadata_for_subjects([first_id, second_id])
        assert set(complete) == {first_id, second_id}
        assert _sql_count(physical, "nngla_municipality_public_read_v2") == 2
        assert physical.connection_instance.municipality_identity_calls == 1

        again = repository.metadata_for_subjects([first_id, second_id])
        assert set(again) == {first_id, second_id}
        assert _sql_count(physical, "nngla_municipality_public_read_v2") == 2

    assert physical.borrow_count == 1


def test_failed_municipality_identity_validation_does_not_poison_request_materialization():
    pool, physical = _layer_pool(invalid_municipality_once=True)
    repository = PostgreSQLMunicipalityPublicMapRepository(pool, runtime_mode="simulation")

    with pool.read_session():
        try:
            repository.governed_ids()
        except NNGLAMapReadAuthorityError:
            pass
        else:
            raise AssertionError("expected invalid 23-ID MUNICIPALITY set to fail")

        governed = repository.governed_ids()
        assert len(governed) == EXPECTED_MUNICIPALITY_COUNT
        assert physical.connection_instance.municipality_identity_calls == 2

    assert physical.borrow_count == 1


def test_city_district_governed_ids_and_records_are_reused_with_complete_set_fallback():
    pool, physical = _layer_pool()
    repository = PostgreSQLCityDistrictPublicMapRepository(pool, runtime_mode="simulation")
    bounds = MapBounds(29.0, -8.0, 45.0, 8.0)
    first_id, second_id = _district_ids()

    with pool.read_session():
        assert repository.governed_ids() == frozenset(_district_ids())
        assert repository.governed_ids() == frozenset(_district_ids())
        assert _sql_count(physical, "parent.administrative_type_code='CITY'") == 1

        page = repository.list_features(bounds=bounds, limit=2000)
        assert [item.subject_id for item in page.items] == [first_id]
        assert _sql_count(physical, "nngla_city_district_public_read_v2") == 1

        cached = repository.metadata_for_subjects([first_id])
        assert set(cached) == {first_id}
        assert _sql_count(physical, "nngla_city_district_public_read_v2") == 1

        complete = repository.metadata_for_subjects([first_id, second_id])
        assert set(complete) == {first_id, second_id}
        assert _sql_count(physical, "nngla_city_district_public_read_v2") == 2
        assert _sql_count(physical, "parent.administrative_type_code='CITY'") == 1

        again = repository.metadata_for_subjects([first_id, second_id])
        assert set(again) == {first_id, second_id}
        assert _sql_count(physical, "nngla_city_district_public_read_v2") == 2

    assert physical.borrow_count == 1


def test_town_governed_ids_and_records_are_reused_with_complete_set_fallback():
    pool, physical = _layer_pool()
    repository = PostgreSQLTownPublicMapRepository(pool, runtime_mode="simulation")
    bounds = MapBounds(29.0, -8.0, 45.0, 8.0)
    first_id, second_id = _town_ids()

    with pool.read_session():
        assert repository.governed_ids() == frozenset(_town_ids())
        assert repository.governed_ids() == frozenset(_town_ids())
        assert _sql_count(physical, "upper(place_type_code)='TOWN'") == 1

        page = repository.list_features(bounds=bounds, limit=2000)
        assert [item.subject_id for item in page.items] == [first_id]
        assert _sql_count(physical, "nngla_town_public_read_v2") == 1

        cached = repository.metadata_for_subjects([first_id])
        assert set(cached) == {first_id}
        assert _sql_count(physical, "nngla_town_public_read_v2") == 1

        complete = repository.metadata_for_subjects([first_id, second_id])
        assert set(complete) == {first_id, second_id}
        assert _sql_count(physical, "nngla_town_public_read_v2") == 2
        assert _sql_count(physical, "upper(place_type_code)='TOWN'") == 1

        again = repository.metadata_for_subjects([first_id, second_id])
        assert set(again) == {first_id, second_id}
        assert _sql_count(physical, "nngla_town_public_read_v2") == 2

    assert physical.borrow_count == 1
