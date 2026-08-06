import json
from pathlib import Path

from infrastructure.geography import (
    BoundaryIdentity,
    CoordinateReference,
    InMemoryWorldBoundaryRepository,
    WorldBoundaryCandidate,
    WorldGeometryService,
)
from infrastructure.ingestion.geojson.reader import GeoJSONSourceReader


ROOT = Path(__file__).parents[4]


def test_raw_geojson_to_governed_publication_pipeline():
    source = ROOT / "data/novegeo/geography/world-boundary/raw/novegeo_world_boundary_v001.geojson"
    features = GeoJSONSourceReader().read(source.read_bytes())
    feature = features[0]
    properties = feature["properties"]
    candidate = WorldBoundaryCandidate(
        identity=BoundaryIdentity(properties["boundaryId"], properties["boundaryVersion"]),
        dataset_id=properties["datasetId"],
        dataset_version=properties["datasetVersion"],
        source_package_id=properties["sourcePackageId"],
        coordinate_reference=CoordinateReference(),
        geometry=feature["geometry"],
    )
    service = WorldGeometryService(InMemoryWorldBoundaryRepository())
    publication = service.publish_candidate(candidate, publication_id="publication:novegeo:v001", qualification_id="qualification:novegeo:v001")
    assert service.get_active() == publication
    assert publication.geometry["type"] == "MultiPolygon"
    assert publication.extent == (29.0, -8.0, 45.0, 8.0)
