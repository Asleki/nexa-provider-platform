from fastapi.testclient import TestClient
from infrastructure.api.app import create_application
from infrastructure.api.config import InfrastructureSettings
from infrastructure.governance.publication import *
def test_health_and_security_contracts():
    with TestClient(create_application(InfrastructureSettings(environment_name="testing"))) as c:
        r=c.get("/api/v1/health/live")
        assert r.status_code==200 and r.headers["x-content-type-options"]=="nosniff" and r.headers["x-correlation-id"]
        assert c.get("/api/v1/health/ready").json()["status"]=="ready"
def test_publication_etag_contract():
    service=PublicationService(InMemoryPublicationRepository((PublicationRecord("publication:one","dataset:one",1,"One","production","public","active",{"value":1}),)))
    with TestClient(create_application(InfrastructureSettings(environment_name="testing"),service)) as c:
        first=c.get("/api/v1/datasets/publication:one")
        assert first.status_code==200 and first.headers["etag"]
        second=c.get("/api/v1/datasets/publication:one",headers={"if-none-match":first.headers["etag"]})
        assert second.status_code==304
def test_openapi_does_not_expose_database_credentials():
    with TestClient(create_application(InfrastructureSettings(environment_name="testing"))) as c:
        body=str(c.get("/openapi.json").json()).lower()
        assert "pgpassword" not in body and "database password" not in body
