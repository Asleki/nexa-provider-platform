from infrastructure.api.services.nngla_region_map_read_service import (
    PostgreSQLRegionAugmentedNNGLAMapReadService,
    REGION_MAP_INTEGRATION_VERSION,
)
from infrastructure.database.read.nngla_national_map import NationalMapFeature, NationalMapPage
from infrastructure.database.read.nngla_region_public_map import RegionMapMetadata

REGION = NationalMapFeature(
    "NG-ADM-000001","ADMINISTRATIVE_AREA","Orivane Capital Territory",
    "publication:nngla:region:1","NG-GEO-123456",1,"ADMINISTRATIVE_BOUNDARY","POLYGON",
    "NG-CRS-EPSG4326",{"type":"Polygon","coordinates":[[[30,0],[31,0],[31,1],[30,0]]]},
    "SHARED_REFERENCE","NNGLA_ADMIN_TYPE","REGION",4,
)

class Repo:
    runtime_mode = "simulation"
    def list_features(self, **kwargs): return NationalMapPage((REGION,), False, None, 4)
    def get_subject(self, subject_id): return REGION if subject_id == REGION.subject_id else None

class RegionRepo:
    runtime_mode = "simulation"
    def metadata_for_subjects(self, subject_ids):
        if REGION.subject_id not in set(subject_ids): return {}
        return {
            REGION.subject_id: RegionMapMetadata(
                subject_id=REGION.subject_id,
                label_point={"type":"Point","coordinates":[30.5,0.5]},
                area_m2=1000.0,
                perimeter_m=200.0,
            )
        }


def test_service_enriches_existing_endpoint_item_without_new_family_or_endpoint_contract():
    service = PostgreSQLRegionAugmentedNNGLAMapReadService(Repo(), RegionRepo())
    body = service.list_features(
        min_longitude=29,min_latitude=-2,max_longitude=34,max_latitude=2,
        families=["ADMINISTRATIVE_AREA"],limit=2000,
    )
    assert body["authorityId"] == "authority:nngla"
    assert body["count"] == 1
    item = body["items"][0]
    assert item["family"] == "ADMINISTRATIVE_AREA"
    assert item["classificationCode"] == "REGION"
    assert item["labelPoint"] == {"type":"Point","coordinates":[30.5,0.5]}
    assert item["areaM2"] == 1000.0
    assert item["perimeterM"] == 200.0
    assert body["regionMapIntegrationVersion"] == REGION_MAP_INTEGRATION_VERSION
    assert len(body["semanticChecksum"]) == 64


def test_subject_read_uses_same_region_metadata_and_checksum_boundary():
    service = PostgreSQLRegionAugmentedNNGLAMapReadService(Repo(), RegionRepo())
    body = service.get_subject("NG-ADM-000001")
    assert body is not None
    assert body["item"]["administrativeLevel"] == "REGION"
    assert body["item"]["labelAnchorKind"] == "DERIVED_PRESENTATION"
    assert len(body["semanticChecksum"]) == 64
