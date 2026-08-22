from fastapi.testclient import TestClient

from infrastructure.api.app import create_application
from infrastructure.api.app.live_composition import create_application_from_environment
from infrastructure.api.config import InfrastructureSettings
from infrastructure.api.services.nngla_postgresql_read_service import PostgreSQLNNGLAReadService
from infrastructure.database.read.world_boundary import PostgreSQLWorldBoundaryRepository
from infrastructure.geography.service import WorldGeometryService


class FakePool:
    def __init__(self, ready=True, fail_open=False):
        self.ready = ready
        self.fail_open = fail_open
        self.open_calls = 0
        self.close_calls = 0

    def open(self):
        self.open_calls += 1
        if self.fail_open:
            from infrastructure.database.runtime.pool import DatabaseUnavailable
            raise DatabaseUnavailable("offline")

    def readiness(self):
        return self.ready

    def close(self):
        self.close_calls += 1


def test_create_application_database_pool_lifecycle_updates_existing_readiness_field_without_changing_global_ready_contract():
    pool = FakePool(ready=True)
    app = create_application(InfrastructureSettings(environment_name="testing"), database_pool=pool)
    with TestClient(app) as client:
        body = client.get("/api/v1/health/ready").json()
        assert body["status"] == "ready"
        assert body["databaseReady"] is True
        assert pool.open_calls == 1
    assert pool.close_calls == 1


def test_environment_composition_remains_historical_source_backed_by_default():
    app = create_application_from_environment({"INFRA_ENVIRONMENT": "testing"})
    with TestClient(app) as client:
        assert client.get("/api/v1/nngla/status").json()["liveDatabaseMigrationStatus"] == "NOT_EXECUTED"
        assert client.get("/api/v1/geography/world-boundary").json()["boundaryVersion"] == 1


def test_environment_composition_builds_postgresql_read_services_only_when_explicitly_selected():
    env = {
        "INFRA_ENVIRONMENT": "development",
        "INFRA_READ_AUTHORITY": "postgresql",
        "INFRA_NNGLA_READ_RUNTIME": "simulation",
        "PGHOST": "db.example.test",
        "PGPORT": "5432",
        "PGDATABASE": "npp_dev",
        "PGUSER": "npp_api_runtime",
        "PGPASSWORD": "secret-for-test-only",
        "PGSSLMODE": "require",
    }
    app = create_application_from_environment(env)
    assert isinstance(app.state.world_geometry_service, WorldGeometryService)
    assert isinstance(app.state.world_geometry_service.repository, PostgreSQLWorldBoundaryRepository)
    assert isinstance(app.state.nngla_read_service, PostgreSQLNNGLAReadService)
    assert app.state.nngla_read_service.repository.runtime_mode == "simulation"
    assert app.state.database_pool is not None
    assert app.state.database_pool.is_open is False
