from fastapi.testclient import TestClient

from infrastructure.api.app import create_application
from infrastructure.api.config import InfrastructureSettings


def test_world_boundary_and_coordinate_reference_are_public_read_only_contracts():
    with TestClient(create_application(InfrastructureSettings(environment_name="testing"))) as client:
        response = client.get("/api/v1/geography/world-boundary")
        assert response.status_code == 200
        body = response.json()
        assert body["boundaryId"] == "boundary:novegeo:sovereign"
        assert body["geometry"]["type"] == "MultiPolygon"
        assert body["coordinateReference"]["axisOrder"] == ["longitude", "latitude"]
        assert response.headers["etag"].startswith('"sha256:')
        reference = client.get("/api/v1/geography/coordinate-reference")
        assert reference.status_code == 200
        assert reference.json()["authorityCode"] == "4326"
