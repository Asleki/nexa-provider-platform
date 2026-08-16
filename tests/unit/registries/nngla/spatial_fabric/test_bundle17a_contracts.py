from decimal import Decimal
import pytest

from registries.nngla.spatial_fabric.contracts import (
    CoordinateCandidate,
    SpatialNeighborTopology,
    canonical_decimal_text,
    parse_decimal,
)


def test_decimal_contract_preserves_numeric_identity_without_display_rounding():
    assert parse_decimal("34.6153270000") == Decimal("34.6153270000")
    assert canonical_decimal_text(Decimal("34.6153270000")) == "34.615327"
    assert canonical_decimal_text(Decimal("-0.000")) == "0"


def test_coordinate_candidate_is_explicitly_noncanonical_and_defers_land_marine_classification():
    candidate = CoordinateCandidate(
        "coordcand:nngla:" + "a" * 64,
        Decimal("34.1"),
        Decimal("2.2"),
        "NG-CRS-EPSG4326",
        2,
        "UNRESOLVED_PENDING_17B",
        "CANDIDATE_ONLY_NOT_PERSISTED",
    )
    assert candidate.occurrence_count == 2
    with pytest.raises(ValueError):
        CoordinateCandidate(
            "coordcand:nngla:" + "a" * 64, Decimal("34.1"), Decimal("2.2"),
            "NG-CRS-EPSG4326", 1, "LAND", "CANDIDATE_ONLY_NOT_PERSISTED",
        )


def test_topology_contract_allows_real_missing_neighbors_without_fabrication():
    row = SpatialNeighborTopology(
        "NG-SCELL-000001", "", "", "", "", "", "", "", "",
        "EXACT_DECIMAL_CENTER_COORDINATE_PLUS_DECLARED_SPACING", "VALID",
    )
    assert row.north_id == ""
