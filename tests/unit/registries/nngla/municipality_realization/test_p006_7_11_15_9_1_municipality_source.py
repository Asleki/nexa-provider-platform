from pathlib import Path
import json

from registries.nngla.municipality_realization.source import load_municipality_sources


def _municipality(serial: int, region: int):
    mid = f"NG-ADM-{serial:06d}"
    return {
        "type": "Feature",
        "properties": {
            "boundary_candidate_id": f"candidate:{mid}",
            "administrative_area_id": mid,
            "source_record_id": f"MUN-{serial:03d}",
            "administrative_type_code": "MUNICIPALITY",
            "canonical_name": f"Municipality {serial}",
            "parent_source_record_id": f"NGR-{region:02d}",
            "region_code": f"NGR-{region:02d}",
            "geometry_type_code": "POLYGON",
            "crs_code": "NG-CRS-EPSG4326",
            "qualification_status": "QUALIFIED",
            "legalization_status": "APPROVED_FOR_GOVERNED_LIVE_APPLICATION",
            "runtime_effect_scope": "SHARED_REFERENCE",
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[[0,0],[1,0],[1,1],[0,0]]],
        },
    }


def test_bundle19b_reader_requires_exact_24_and_three_per_region(tmp_path: Path):
    municipalities = []
    serial = 1
    for region in range(1, 9):
        for _ in range(3):
            municipalities.append(_municipality(serial, region))
            serial += 1
    filler = [
        {
            "type": "Feature",
            "properties": {"administrative_type_code": "CITY"},
            "geometry": {},
        }
        for _ in range(168)
    ]
    payload = {
        "type": "FeatureCollection",
        "metadata": {
            "dataset_id": "dataset:novegeo:administrative-boundaries",
            "dataset_version": 1,
            "crs_code": "NG-CRS-EPSG4326",
            "feature_count": 192,
            "runtime_effect_scope": "SHARED_REFERENCE",
        },
        "features": municipalities + filler,
    }
    path = tmp_path / "bundle19b.geojson"
    path.write_text(json.dumps(payload), encoding="utf-8")
    rows = load_municipality_sources(path)
    assert len(rows) == 24
    counts = {}
    for row in rows:
        counts[row.region_code] = counts.get(row.region_code, 0) + 1
    assert len(counts) == 8
    assert set(counts.values()) == {3}
