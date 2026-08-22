import json

from fastapi.testclient import TestClient

from infrastructure.api.app import create_application
from infrastructure.api.config import InfrastructureSettings
from infrastructure.api.services.nngla_postgresql_read_service import PostgreSQLNNGLAReadService
from infrastructure.database.read.nngla import PostgreSQLNNGLAReadRepository
from infrastructure.database.read.world_boundary import PostgreSQLWorldBoundaryRepository
from infrastructure.geography.service import WorldGeometryService


class Cursor:
    def __init__(self):
        self.rows = []
        self.row = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        compact = " ".join(sql.split())
        self.rows = []
        self.row = None
        if "FROM geography.world_boundary wb" in compact:
            self.row = (
                "publication:novegeo:world-boundary:v002",
                "boundary:novegeo:sovereign",
                2,
                "dataset:novegeo:world-boundary",
                2,
                "crs:novegeo:geographic",
                1,
                "EPSG",
                "4326",
                ["longitude", "latitude"],
                "decimal_degrees",
                json.dumps({
                    "type": "MultiPolygon",
                    "coordinates": [[[[29.05, -7.717467], [44.805229, -7.717467], [44.805229, 7.85], [29.05, -7.717467]]]],
                }),
                29.05,
                -7.717467,
                44.805229,
                7.85,
                "3" * 64,
                "4" * 64,
                "4" * 64,
                "shared_reference",
                "shared_reference",
                "shared_reference",
                "public",
                "public",
                "public",
                "active",
                "active",
                "qualified",
                "dataset:novegeo:world-boundary",
            )
        elif "SUM(a.row_count)" in compact and "GROUP BY d.dataset_id" in compact:
            self.rows = [
                ("dataset:novegeo:places:v001:700", "1", 700),
                ("dataset:novegeo:administrative-areas:v001:192", "1", 192),
                ("dataset:novegeo:geographic-features:v001:21", "1", 21),
                ("dataset:novegeo:roads:v001:900", "1", 900),
            ]
        elif "UNION ALL" in compact and "nngla_place_reference" in compact:
            self.rows = [
                ("PLACE", 700),
                ("ADMINISTRATIVE_AREA", 192),
                ("GEOGRAPHIC_FEATURE", 21),
                ("ROAD", 350),
                ("ADDRESS", 0),
                ("PARCEL", 0),
            ]
        elif "GROUP BY record_family" in compact:
            self.rows = []
        elif "MAX(read_model_version)" in compact:
            self.row = (1,)
        elif "nngla_canonical_crosswalk" in compact and "SUM(a.row_count)" in compact:
            self.row = (2411, 2411)
        elif "ORDER BY subject_id" in compact and "nngla_spatial_read_projection_v1" in compact:
            self.rows = []
        elif compact == "SELECT 1":
            self.row = (1,)
        else:
            raise AssertionError(f"Unexpected SQL: {compact}")

    def fetchall(self):
        return list(self.rows)

    def fetchone(self):
        return self.row


class Connection:
    def __init__(self, cursor):
        self._cursor = cursor

    def cursor(self):
        return self._cursor


class Context:
    def __init__(self, value):
        self.value = value

    def __enter__(self):
        return self.value

    def __exit__(self, exc_type, exc, tb):
        return False


class Pool:
    def __init__(self):
        self.cursor_ref = Cursor()
        self.read_only_calls = []
        self.open_calls = 0
        self.close_calls = 0

    def open(self):
        self.open_calls += 1

    def close(self):
        self.close_calls += 1

    def readiness(self):
        return True

    def connection(self, read_only=False):
        self.read_only_calls.append(read_only)
        return Context(Connection(self.cursor_ref))


def build_live_app():
    pool = Pool()
    return (
        create_application(
            InfrastructureSettings(environment_name="testing"),
            world_geometry_service=WorldGeometryService(PostgreSQLWorldBoundaryRepository(pool)),
            nngla_read_service=PostgreSQLNNGLAReadService(PostgreSQLNNGLAReadRepository(pool, runtime_mode="simulation")),
            database_pool=pool,
        ),
        pool,
    )


def test_p006_7_11_8_world_boundary_route_returns_postgresql_v002_using_existing_public_contract():
    app, pool = build_live_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/geography/world-boundary")
        assert response.status_code == 200
        body = response.json()
        assert body["publicationId"] == "publication:novegeo:world-boundary:v002"
        assert body["boundaryId"] == "boundary:novegeo:sovereign"
        assert body["boundaryVersion"] == 2
        assert body["datasetVersion"] == 2
        assert body["geometry"]["type"] == "MultiPolygon"
        assert body["coordinateReference"]["authorityCode"] == "4326"
        assert body["coordinateReference"]["axisOrder"] == ["longitude", "latitude"]
        assert body["extent"] == {
            "minLongitude": 29.05,
            "minLatitude": -7.717467,
            "maxLongitude": 44.805229,
            "maxLatitude": 7.85,
        }
        assert response.headers["etag"] == f'"sha256:{"4" * 64}"'
    assert pool.read_only_calls and all(pool.read_only_calls)


def test_p006_7_11_8_live_nngla_status_reports_database_truth_but_zero_public_projection():
    app, _pool = build_live_app()
    with TestClient(app) as client:
        response = client.get("/api/v1/nngla/status")
        assert response.status_code == 200
        body = response.json()
        assert body["liveDatabaseMigrationStatus"] == "EXECUTED"
        assert body["databaseAuthority"] == "SERVER_SIDE_ONLY"
        assert body["readRuntime"] == "simulation"
        families = {item["family"]: item for item in body["families"]}
        assert families["PLACE"]["canonicalCount"] == 700
        assert families["ADMINISTRATIVE_AREA"]["canonicalCount"] == 192
        assert families["ROAD"]["sourceCount"] == 900
        assert families["ROAD"]["canonicalCount"] == 350
        assert families["GEOGRAPHIC_FEATURE"]["canonicalCount"] == 21
        assert all(item["publishedCount"] == 0 for item in body["families"])
        assert all(item["mapRenderableCount"] == 0 for item in body["families"])

        places = client.get("/api/v1/nngla/places").json()
        assert places["items"] == []
        assert places["canonicalCount"] == 700
        assert places["publishedCount"] == 0
