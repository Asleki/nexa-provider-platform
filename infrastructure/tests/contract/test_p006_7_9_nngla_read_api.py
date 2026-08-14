from fastapi.testclient import TestClient

from infrastructure.api.app import create_application
from infrastructure.api.config import InfrastructureSettings


def test_p006_7_9_nngla_status_is_read_only_privacy_safe_and_truthful():
    with TestClient(create_application(InfrastructureSettings(environment_name="testing"))) as client:
        response = client.get("/api/v1/nngla/status")
        assert response.status_code == 200
        body = response.json()
        assert body["authorityId"] == "authority:nngla"
        assert body["countryId"] == "country:novegeo"
        assert body["databaseAuthority"] == "SERVER_SIDE_ONLY"
        assert body["liveDatabaseMigrationStatus"] == "NOT_EXECUTED"
        families = {item["family"]: item for item in body["families"]}
        assert families["PLACE"]["sourceCount"] == 700
        assert families["ROAD"]["sourceCount"] == 900
        assert families["GEOGRAPHIC_FEATURE"]["sourceCount"] == 21
        assert families["ADMINISTRATIVE_AREA"]["sourceCount"] == 192
        assert all(item["canonicalCount"] == 0 for item in body["families"])
        assert families["ADDRESS"]["sourceCount"] == 0
        assert families["PARCEL"]["sourceCount"] == 0
        assert all(item["publishedCount"] == 0 and item["mapRenderableCount"] == 0 for item in body["families"])
        assert response.headers["etag"].startswith('"sha256:')
        assert response.headers["cache-control"] == "public, max-age=60"
        cached = client.get("/api/v1/nngla/status", headers={"if-none-match": response.headers["etag"]})
        assert cached.status_code == 304


def test_p006_7_9_public_domain_routes_do_not_leak_provisional_or_legal_holder_data():
    with TestClient(create_application(InfrastructureSettings(environment_name="testing"))) as client:
        for path, expected_known in (("places", 700), ("roads", 900), ("addresses", 0), ("parcels", 0)):
            response = client.get(f"/api/v1/nngla/{path}")
            assert response.status_code == 200
            body = response.json()
            assert body["count"] == 0
            assert body["sourceCount"] == expected_known
            assert body["items"] == []
            lowered = response.text.lower()
            assert "holder_reference" not in lowered
            assert "titleholder" not in lowered


def test_p006_7_9_unknown_public_family_is_not_exposed_and_post_is_not_available():
    with TestClient(create_application(InfrastructureSettings(environment_name="testing"))) as client:
        assert client.get("/api/v1/nngla/titles").status_code == 404
        assert client.post("/api/v1/nngla/places", json={}).status_code == 405
