from decimal import Decimal

from registries.nngla.spatial_fabric.bundle17b.precision import (
    derive_precision_qualifications,
    precision_findings,
)


def test_every_coordinate_occurrence_has_two_axis_level_precision_evidence_rows():
    rows = derive_precision_qualifications()
    assert len(rows) == 10644
    assert precision_findings(rows) == ()
    assert sum(row.axis == "LONGITUDE" for row in rows) == 5322
    assert sum(row.axis == "LATITUDE" for row in rows) == 5322


def test_canonical_numeric_value_never_moves_when_trailing_zero_or_source_precision_changes():
    rows = derive_precision_qualifications()
    assert all(Decimal(row.source_value) == Decimal(row.canonical_value) for row in rows)
    assert all(row.round_trip_same_location for row in rows)
    assert all(not row.display_is_authoritative for row in rows)


def test_human_display_rounding_is_bounded_without_replacing_nine_decimal_canonical_coordinates():
    rows = derive_precision_qualifications()
    high_precision = [row for row in rows if row.source_decimal_places > 6]
    assert high_precision
    assert max(row.source_decimal_places for row in rows) == 9
    assert all(row.display_decimal_places <= 6 for row in rows)
    assert any(row.display_value != row.canonical_value for row in high_precision)
