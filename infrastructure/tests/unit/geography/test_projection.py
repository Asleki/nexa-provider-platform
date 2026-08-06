import pytest

from infrastructure.geography import EquirectangularWorldProjection, GeographicCoordinate


def test_forward_and_inverse_projection_round_trip():
    projection = EquirectangularWorldProjection()
    source = GeographicCoordinate(34.25, -1.5)
    projected = projection.forward(source)
    restored = projection.inverse(projected)
    assert restored.longitude == pytest.approx(source.longitude, abs=projection.tolerance)
    assert restored.latitude == pytest.approx(source.latitude, abs=projection.tolerance)


def test_projection_maps_global_extremes_to_normalized_world():
    projection = EquirectangularWorldProjection()
    assert projection.forward(GeographicCoordinate(-180, 90)).x == 0
    assert projection.forward(GeographicCoordinate(-180, 90)).y == 0
    assert projection.forward(GeographicCoordinate(180, -90)).x == 1
    assert projection.forward(GeographicCoordinate(180, -90)).y == 1
