from fastapi import FastAPI
from fastapi.testclient import TestClient
from infrastructure.api.routers.nngla_map import router

class Service:
    def list_features(self,**kwargs): return {"semanticChecksum":"a"*64,"items":[],"count":0}
    def get_subject(self,subject_id): return None

def test_map_router_has_separate_non_ambiguous_namespace_and_etag():
    app=FastAPI(); app.state.nngla_map_read_service=Service(); app.include_router(router,prefix="/api/v1")
    client=TestClient(app)
    response=client.get("/api/v1/nngla-map/features?minLongitude=30&minLatitude=-20&maxLongitude=32&maxLatitude=-17")
    assert response.status_code==200
    assert response.headers["etag"]=='"sha256:'+('a'*64)+'"'

def test_exact_subject_resolution_is_public_only_not_found():
    app=FastAPI(); app.state.nngla_map_read_service=Service(); app.include_router(router,prefix="/api/v1")
    response=TestClient(app).get("/api/v1/nngla-map/subjects/NG-PLC-999999")
    assert response.status_code==404
