from infrastructure.api.services.nngla_map_read_service import PostgreSQLNNGLAMapReadService
from infrastructure.database.read.nngla_national_map import NationalMapFeature, NationalMapPage

FEATURE=NationalMapFeature("NG-RD-000001","ROAD","Road 1","publication:nngla:road:1","NG-GEO-000901",1,"ROAD_ALIGNMENT","LINESTRING","NG-CRS-EPSG4326",{"type":"LineString","coordinates":[[30,-18],[31,-18]]},"SHARED_REFERENCE","NNGLA_ROAD_CLASS","REGIONAL",3)
class Repo:
    runtime_mode="simulation"
    def list_features(self,**kwargs): return NationalMapPage((FEATURE,),False,None,3)
    def get_subject(self,subject_id): return FEATURE if subject_id==FEATURE.subject_id else None

def test_service_returns_stable_identity_geometry_and_semantic_checksum():
    body=PostgreSQLNNGLAMapReadService(Repo()).list_features(min_longitude=30,min_latitude=-20,max_longitude=32,max_latitude=-17,families=["ROAD"],limit=50)
    assert body["readRuntime"]=="simulation"
    assert body["items"][0]["subjectId"]=="NG-RD-000001"
    assert body["items"][0]["geometryId"]=="NG-GEO-000901"
    assert len(body["semanticChecksum"])==64
    assert body["privacyBoundary"]=="PUBLIC_READ_MODELS_ONLY"
