from types import SimpleNamespace

import psycopg_pool

from infrastructure.database.runtime.pool import PostgreSQLPool


class RecordingConnectionPool:
    last_kwargs = None

    @staticmethod
    def check_connection(connection):
        return None

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs

    def close(self):
        return None


def test_postgresql_pool_checks_connection_before_borrow(monkeypatch):
    monkeypatch.setattr(
        psycopg_pool,
        "ConnectionPool",
        RecordingConnectionPool,
    )

    settings = SimpleNamespace(
        host="db.example.test",
        port=5432,
        database_name="npp_test",
        username="npp_test",
        password="test-only",
        ssl_mode="require",
        min_pool_size=1,
        max_pool_size=5,
        acquisition_timeout_seconds=10,
    )

    pool = PostgreSQLPool(settings)
    pool.open()

    kwargs = RecordingConnectionPool.last_kwargs

    assert kwargs is not None
    assert kwargs["check"] is RecordingConnectionPool.check_connection
    assert kwargs["min_size"] == 1
    assert kwargs["max_size"] == 5
    assert kwargs["timeout"] == 10
    assert kwargs["open"] is True
