from contextlib import contextmanager
from types import SimpleNamespace
import threading

from infrastructure.database.runtime.pool import PostgreSQLPool


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
        host="db.test", port=5432, database_name="npp", username="npp",
        password="test", ssl_mode="require", min_pool_size=1, max_pool_size=5,
        acquisition_timeout_seconds=10,
    )


def test_nested_repository_style_reads_reuse_one_physical_checked_lease():
    physical = FakePhysicalPool()
    pool = PostgreSQLPool(settings(), pool_factory=lambda _settings: physical)
    pool.open()

    with pool.read_session() as request_connection:
        with pool.connection(read_only=True) as first:
            with pool.connection(read_only=True) as second:
                assert first is request_connection
                assert second is request_connection

    assert physical.borrow_count == 1
    assert physical.connections[0].sql == ["SET TRANSACTION READ ONLY"]


def test_reads_outside_request_scope_preserve_historical_independent_borrows():
    physical = FakePhysicalPool()
    pool = PostgreSQLPool(settings(), pool_factory=lambda _settings: physical)
    pool.open()

    with pool.connection(read_only=True):
        pass
    with pool.connection(read_only=True):
        pass

    assert physical.borrow_count == 2
    assert [connection.sql for connection in physical.connections] == [
        ["SET TRANSACTION READ ONLY"],
        ["SET TRANSACTION READ ONLY"],
    ]


def test_context_local_read_sessions_do_not_share_connections_across_threads():
    physical = FakePhysicalPool()
    pool = PostgreSQLPool(settings(), pool_factory=lambda _settings: physical)
    pool.open()
    barrier = threading.Barrier(2)
    seen = []

    def worker():
        with pool.read_session() as request_connection:
            barrier.wait(timeout=5)
            with pool.connection(read_only=True) as nested:
                seen.append((request_connection.name, nested.name))

    threads = [threading.Thread(target=worker) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=5)

    assert not any(thread.is_alive() for thread in threads)
    assert physical.borrow_count == 2
    assert len({request for request, _ in seen}) == 2
    assert all(request == nested for request, nested in seen)
