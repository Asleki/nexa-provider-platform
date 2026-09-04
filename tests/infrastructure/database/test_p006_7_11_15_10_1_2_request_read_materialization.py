from contextlib import contextmanager
from types import SimpleNamespace
import threading

import pytest

from infrastructure.database.runtime.pool import DatabaseUnavailable, PostgreSQLPool
from infrastructure.database.runtime.read_materialization import (
    RequestReadMaterialization,
    current_request_read_materialization,
    materialization_key,
)


class FakeCursor:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, sql):
        self.connection.sql.append(sql)


class FakeConnection:
    def __init__(self, name):
        self.name = name
        self.sql = []

    def cursor(self):
        return FakeCursor(self)


class FakePhysicalPool:
    def __init__(self):
        self.borrow_count = 0
        self.connections = []
        self._lock = threading.Lock()

    @contextmanager
    def connection(self):
        with self._lock:
            self.borrow_count += 1
            connection = FakeConnection(f"connection-{self.borrow_count}")
            self.connections.append(connection)
        yield connection

    def close(self):
        return None


def settings():
    return SimpleNamespace(
        host="db.test",
        port=5432,
        database_name="npp",
        username="npp",
        password="test",
        ssl_mode="require",
        min_pool_size=1,
        max_pool_size=5,
        acquisition_timeout_seconds=10,
    )


def test_materialization_supports_namespaced_values_and_complete_subject_sets():
    materialization = RequestReadMaterialization()
    sim_key = materialization_key("simulation", "nngla.region.records")
    prod_key = materialization_key("production", "nngla.region.records")

    materialization.set(sim_key, "opaque")
    assert materialization.get(sim_key) == "opaque"
    assert materialization.get(prod_key) is None

    records_key = materialization_key("simulation", "nngla.city.records")
    materialization.merge_mapping(records_key, {"A": 1})
    assert materialization.complete_mapping(records_key, ["A"]) == {"A": 1}
    assert materialization.complete_mapping(records_key, ["A", "B"]) is None

    materialization.merge_mapping(records_key, {"B": 2})
    assert materialization.complete_mapping(records_key, ["A", "B"]) == {"A": 1, "B": 2}


def test_outer_read_session_owns_one_materialization_and_nested_session_reuses_it():
    physical = FakePhysicalPool()
    pool = PostgreSQLPool(settings(), pool_factory=lambda _settings: physical)
    pool.open()

    assert pool.current_read_materialization() is None
    with pool.read_session() as request_connection:
        first = pool.current_read_materialization()
        assert isinstance(first, RequestReadMaterialization)
        assert current_request_read_materialization(pool) is first
        with pool.read_session() as nested_connection:
            assert nested_connection is request_connection
            assert pool.current_read_materialization() is first

    assert physical.borrow_count == 1
    assert pool.current_read_materialization() is None


def test_sequential_read_sessions_never_share_materialized_values():
    physical = FakePhysicalPool()
    pool = PostgreSQLPool(settings(), pool_factory=lambda _settings: physical)
    pool.open()
    key = materialization_key("simulation", "nngla.test")

    with pool.read_session():
        first = pool.current_read_materialization()
        first.set(key, "first")

    with pool.read_session():
        second = pool.current_read_materialization()
        assert second is not first
        assert second.get(key) is None

    assert physical.borrow_count == 2


def test_failed_read_session_resets_connection_and_materialization_contexts():
    physical = FakePhysicalPool()
    pool = PostgreSQLPool(settings(), pool_factory=lambda _settings: physical)
    pool.open()

    with pytest.raises(DatabaseUnavailable, match="database operation failed") as exc_info:
        with pool.read_session():
            assert pool.current_read_materialization() is not None
            raise RuntimeError("boom")

    assert isinstance(exc_info.value.__cause__, RuntimeError)
    assert str(exc_info.value.__cause__) == "boom"
    assert pool.current_read_materialization() is None
    with pool.connection(read_only=True):
        pass
    assert physical.borrow_count == 2


def test_contextvars_keep_materialization_request_local_across_threads():
    physical = FakePhysicalPool()
    pool = PostgreSQLPool(settings(), pool_factory=lambda _settings: physical)
    pool.open()
    barrier = threading.Barrier(2)
    materializations = []

    def worker():
        with pool.read_session():
            materialization = pool.current_read_materialization()
            barrier.wait(timeout=5)
            materializations.append(materialization)

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not any(thread.is_alive() for thread in threads)
    assert physical.borrow_count == 2
    assert len(materializations) == 2
    assert materializations[0] is not materializations[1]


def test_fake_or_legacy_pool_without_materialization_api_remains_compatible():
    class LegacyPool:
        pass

    assert current_request_read_materialization(LegacyPool()) is None
