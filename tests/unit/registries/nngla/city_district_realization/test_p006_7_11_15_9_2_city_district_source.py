from collections import Counter
from pathlib import Path

import pytest

from registries.nngla.city_district_realization.contracts import (
    EXPECTED_CITY_DISTRICT_COUNT,
    EXPECTED_PER_CITY,
    SOURCE_DATASET_ID,
    SOURCE_DATASET_SHA256,
    SOURCE_DATASET_VERSION,
)
from registries.nngla.city_district_realization.source import (
    load_city_district_sources,
)


ROOT = Path(__file__).resolve().parents[5]

SOURCE = (
    ROOT
    / "data/novegeo/nngla/spatial-fabric/bundle19b/qualified/"
      "novegeo_administrative_boundaries_v001.geojson"
)


def test_locked_bundle19b_city_district_source_contract():
    rows = load_city_district_sources(SOURCE)

    assert len(rows) == EXPECTED_CITY_DISTRICT_COUNT == 64

    assert {
        row.source_dataset_id
        for row in rows
    } == {
        SOURCE_DATASET_ID
    }

    assert {
        row.source_dataset_version
        for row in rows
    } == {
        SOURCE_DATASET_VERSION
    }

    assert {
        row.source_dataset_sha256
        for row in rows
    } == {
        SOURCE_DATASET_SHA256
    }

    assert {
        row.geometry_type_code
        for row in rows
    } <= {
        "POLYGON",
        "MULTIPOLYGON",
    }

    parent_counts = Counter(
        row.parent_source_record_id
        for row in rows
    )

    assert len(parent_counts) == 8

    assert set(
        parent_counts.values()
    ) == {
        EXPECTED_PER_CITY
    }


def test_bundle19b_sha_pin_fails_closed_on_tampering(tmp_path):
    tampered = (
        tmp_path
        / "novegeo_administrative_boundaries_v001.geojson"
    )

    tampered.write_bytes(
        SOURCE.read_bytes() + b"\n"
    )

    with pytest.raises(
        ValueError,
        match="SHA-256 changed",
    ):
        load_city_district_sources(
            tampered
        )
