from contextlib import contextmanager
from types import SimpleNamespace

from fastapi import Response

from infrastructure.api.routers.nngla_map import list_map_features
from infrastructure.database.runtime.pool import PostgreSQLPool


class FakeCursor:
    def __init__(self, connection): self.connection = connection
    def __enter__(self): return self
    def __exit__(self, *_args): return False
    def execute(self, sql): self.connection.sql.append(sql)


class FakeConnection:
    def __init__(self): self.sql = []
    def cursor(self): return FakeCursor(self)


class FakePhysicalPool:
    def __init__(self): self.borrow_count = 0
    @contextmanager
    def connection(self):
        self.borrow_count += 1
        yield FakeConnection()
    def close(self): pass


class RepositoryStyleService:
    def __init__(self, pool): self.pool = pool
    def list_features(self, **_kwargs):
        for _ in range(19):
            with self.pool.connection(read_only=True):
                pass
        return {
            "semanticChecksum": "a" * 64,
            "items": [],
            "count": 0,
        }


def test_map_router_reduces_nineteen_repository_scopes_to_one_physical_acquisition():
    settings = SimpleNamespace(host="db", port=5432, database_name="npp", username="npp", password="test", ssl_mode="require", min_pool_size=1, max_pool_size=5, acquisition_timeout_seconds=10)
    physical = FakePhysicalPool()
    pool = PostgreSQLPool(settings, pool_factory=lambda _settings: physical)
    pool.open()
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database_pool=pool, nngla_map_read_service=RepositoryStyleService(pool))))
    response = Response()

    body = list_map_features(
        request=request,
        response=response,
        min_longitude=29.05,
        min_latitude=-7.7,
        max_longitude=44.8,
        max_latitude=7.8,
        family=None,
        limit=2000,
        cursor=None,
        if_none_match=None,
    )

    assert body["count"] == 0
    assert physical.borrow_count == 1
    assert response.headers["etag"] == f'"sha256:{"a" * 64}"'


def test_map_router_preserves_source_authority_composition_without_database_pool():
    service = SimpleNamespace(list_features=lambda **_kwargs: {"semanticChecksum": "b" * 64, "items": [], "count": 0})
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(database_pool=None, nngla_map_read_service=service)))
    response = Response()
    body = list_map_features(request=request, response=response, min_longitude=29, min_latitude=-8, max_longitude=45, max_latitude=8, family=None, limit=2000, cursor=None, if_none_match=None)
    assert body["count"] == 0
