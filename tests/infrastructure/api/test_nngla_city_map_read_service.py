from infrastructure.api.services.nngla_city_map_read_service import (
    CITY_MAP_INTEGRATION_VERSION,
    PostgreSQLCityAugmentedNNGLAMapReadService,
)
from infrastructure.database.read.nngla_city_public_map import CityMapMetadata
from infrastructure.database.read.nngla_national_map import NationalMapFeature, NationalMapPage
from infrastructure.database.read.nngla_region_public_map import RegionMapMetadata

CITY = NationalMapFeature(
    "NG-ADM-000170","ADMINISTRATIVE_AREA","Port Meridian",
    "city-publication:nngla:port-meridian","city-geometry:nngla:NG-ADM-000170:v1",1,
    "ADMINISTRATIVE_BOUNDARY","POLYGON","NG-CRS-EPSG4326",
    {"type":"Polygon","coordinates":[[[42.8,0.1],[43.3,0.1],[43.3,0.7],[42.8,0.1]]]},
    "SHARED_REFERENCE","NNGLA_ADMIN_TYPE","CITY",8,
)
REGION = NationalMapFeature(
    "NG-ADM-000008","ADMINISTRATIVE_AREA","Sabaran Gulf",
    "region-publication:nngla:8","region-geometry:nngla:NG-ADM-000008:v1",1,
    "ADMINISTRATIVE_BOUNDARY","MULTIPOLYGON","NG-CRS-EPSG4326",
    {"type":"MultiPolygon","coordinates":[]},"SHARED_REFERENCE","NNGLA_ADMIN_TYPE","REGION",7,
)

class Repo:
    runtime_mode = "simulation"
    def list_features(self, **kwargs): return NationalMapPage((REGION, CITY), False, None, 8)
    def get_subject(self, subject_id):
        return CITY if subject_id == CITY.subject_id else REGION if subject_id == REGION.subject_id else None

class RegionRepo:
    runtime_mode = "simulation"
    def metadata_for_subjects(self, subject_ids):
        if REGION.subject_id not in set(subject_ids): return {}
        return {REGION.subject_id: RegionMapMetadata(REGION.subject_id,{"type":"Point","coordinates":[43,-2]},1000.0,200.0)}

class CityRepo:
    runtime_mode = "simulation"
    def metadata_for_subjects(self, subject_ids):
        if CITY.subject_id not in set(subject_ids): return {}
        return {CITY.subject_id: CityMapMetadata(CITY.subject_id,"NG-ADM-000008",{"type":"Point","coordinates":[43,0.35]},120.0,45.0)}


def test_city_service_preserves_region_enrichment_and_adds_city_metadata():
    service = PostgreSQLCityAugmentedNNGLAMapReadService(Repo(), RegionRepo(), CityRepo())
    body = service.list_features(
        min_longitude=29,min_latitude=-8,max_longitude=45,max_latitude=8,
        families=["ADMINISTRATIVE_AREA"],limit=2000,
    )
    by_id = {item["subjectId"]: item for item in body["items"]}
    assert by_id[REGION.subject_id]["administrativeLevel"] == "REGION"
    assert by_id[CITY.subject_id]["administrativeLevel"] == "CITY"
    assert by_id[CITY.subject_id]["parentRegionId"] == "NG-ADM-000008"
    assert by_id[CITY.subject_id]["areaM2"] == 120.0
    assert body["cityMapIntegrationVersion"] == CITY_MAP_INTEGRATION_VERSION
    assert body["regionMapIntegrationVersion"] >= 1
    assert len(body["semanticChecksum"]) == 64


def test_city_subject_read_uses_same_new_city_metadata_and_checksum_boundary():
    service = PostgreSQLCityAugmentedNNGLAMapReadService(Repo(), RegionRepo(), CityRepo())
    body = service.get_subject(CITY.subject_id)
    assert body is not None
    assert body["item"]["parentRegionId"] == "NG-ADM-000008"
    assert body["item"]["labelAnchorKind"] == "DERIVED_PRESENTATION"
    assert body["cityMapIntegrationVersion"] == 1
    assert len(body["semanticChecksum"]) == 64
