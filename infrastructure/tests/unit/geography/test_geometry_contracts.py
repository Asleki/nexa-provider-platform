import pytest

from infrastructure.geography import (
    BoundaryIdentity,
    BoundaryValidationError,
    CoordinateReference,
    GeographicCoordinate,
    WorldBoundaryCandidate,
    WorldBoundaryQualificationService,
    normalize_boundary_geometry,
)


def candidate(geometry):
    return WorldBoundaryCandidate(
        identity=BoundaryIdentity("boundary:novegeo:sovereign", 1),
        dataset_id="dataset:novegeo:world-boundary",
        dataset_version=1,
        source_package_id="source-package:novegeo:world-boundary:v001",
        coordinate_reference=CoordinateReference(),
        geometry=geometry,
    )


def test_polygon_is_normalized_to_multipolygon_and_qualified_deterministically():
    geometry = {"type": "Polygon", "coordinates": [[[30, -6], [36, -8], [42, -4], [45, 2], [41, 7], [34, 8], [29, 3], [30, -6]]]}
    normalized = normalize_boundary_geometry(geometry)
    assert normalized["type"] == "MultiPolygon"
    receipt = WorldBoundaryQualificationService().qualify(candidate(geometry), qualification_id="qualification:novegeo:v001")
    assert receipt.decision == "qualified"
    assert receipt.extent == (29.0, -8.0, 45.0, 8.0)
    assert len(receipt.content_sha256) == 64


@pytest.mark.parametrize(
    "geometry",
    [
        {"type": "Point", "coordinates": [30, 0]},
        {"type": "Polygon", "coordinates": [[[30, 0], [31, 1], [32, 0]]]},
        {"type": "Polygon", "coordinates": [[[30, 0], [31, 1], [32, 0], [30, 1]]]},
        {"type": "Polygon", "coordinates": [[[181, 0], [31, 1], [32, 0], [181, 0]]]},
    ],
)
def test_invalid_boundary_shapes_are_rejected(geometry):
    with pytest.raises(BoundaryValidationError):
        normalize_boundary_geometry(geometry)


def test_zero_longitude_and_equator_are_valid_coordinates():
    assert GeographicCoordinate(0, 0).to_pair() == (0, 0)
