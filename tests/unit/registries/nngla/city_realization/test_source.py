import json
from pathlib import Path

from registries.nngla.city_realization.contracts import OFFICIAL_NOVEGEO_CITY_IDS
from registries.nngla.city_realization.source import load_city_sources


def _feature(city_id, ordinal):
    return {
        "type": "Feature",
        "id": f"feature-{ordinal}",
        "properties": {
            "boundary_candidate_id": f"candidate-{ordinal}",
            "administrative_area_id": city_id,
            "source_record_id": f"SRC-{ordinal}",
            "administrative_type_code": "CITY",
            "canonical_name": f"City {ordinal}",
            "region_code": f"NGR-{ordinal:02d}",
            "geometry_type_code": "POLYGON",
            "crs_code": "NG-CRS-EPSG4326",
            "qualification_status": "QUALIFIED",
            "legalization_status": "APPROVED_FOR_GOVERNED_LIVE_APPLICATION",
            "runtime_effect_scope": "SHARED_REFERENCE",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[ordinal, 0], [ordinal + 0.5, 0], [ordinal, 0.5], [ordinal, 0]]],
        },
    }


def test_loader_extracts_exact_eight_official_cities_from_192_feature_artifact(tmp_path: Path):
    cities = [_feature(city_id, index) for index, city_id in enumerate(OFFICIAL_NOVEGEO_CITY_IDS, 1)]
    filler = []
    for index in range(184):
        filler.append({
            "type": "Feature",
            "properties": {"administrative_type_code": "TOWNSHIP"},
            "geometry": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[0,1],[0,0]]]},
        })
    artifact = {
        "type": "FeatureCollection",
        "metadata": {
            "dataset_id": "dataset:novegeo:administrative-boundaries",
            "dataset_version": 1,
            "feature_count": 192,
            "crs_code": "NG-CRS-EPSG4326",
            "runtime_effect_scope": "SHARED_REFERENCE",
        },
        "features": cities + filler,
    }
    path = tmp_path / "boundaries.geojson"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    rows = load_city_sources(path)
    assert tuple(row.administrative_area_id for row in rows) == OFFICIAL_NOVEGEO_CITY_IDS
    assert all(len(row.source_dataset_sha256) == 64 for row in rows)
    assert all(len(row.source_geometry_sha256) == 64 for row in rows)


def test_loader_rejects_unknown_city_identity(tmp_path: Path):
    cities = [_feature(city_id, index) for index, city_id in enumerate(OFFICIAL_NOVEGEO_CITY_IDS, 1)]
    cities[0]["properties"]["administrative_area_id"] = "NG-ADM-999999"
    filler = [{
        "type": "Feature",
        "properties": {"administrative_type_code": "TOWNSHIP"},
        "geometry": {"type": "Polygon", "coordinates": [[[0,0],[1,0],[0,1],[0,0]]]},
    } for _ in range(184)]
    path = tmp_path / "bad.geojson"
    path.write_text(json.dumps({
        "metadata": {
            "dataset_id": "dataset:novegeo:administrative-boundaries",
            "dataset_version": 1,
            "feature_count": 192,
            "crs_code": "NG-CRS-EPSG4326",
            "runtime_effect_scope": "SHARED_REFERENCE",
        },
        "features": cities + filler,
    }), encoding="utf-8")
    try:
        load_city_sources(path)
    except ValueError as exc:
        assert "unexpected CITY identity" in str(exc)
    else:
        raise AssertionError("unknown CITY must fail closed")
