"""Load governed geometry payloads referenced by NNGLA geometry candidates."""
from __future__ import annotations
import json
from .source_catalogue import ROOT, SourceRecord

class GeometryPayloadError(ValueError):
    pass

def load_geometry(record: SourceRecord) -> dict[str, object]:
    p = record.payload
    path = ROOT / str(p.get("source_path_reference", ""))
    if not path.is_file():
        raise GeometryPayloadError(f"geometry source does not exist: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    subject_id = str(p.get("subject_id", ""))
    if path.suffix.lower() == ".geojson" or payload.get("type") == "FeatureCollection":
        if subject_id == "country:novegeo":
            features = payload.get("features") or []
            if len(features) != 1:
                raise GeometryPayloadError("sovereign geometry must contain exactly one feature")
            geometry = features[0].get("geometry")
        else:
            feature = next((f for f in payload.get("features", []) if str(f.get("id") or (f.get("properties") or {}).get("landformId")) == subject_id), None)
            geometry = feature.get("geometry") if feature else None
    else:
        geometry = None
        for family, key in (("rivers", "riverId"), ("lakes", "lakeId")):
            item = next((x for x in payload.get(family, []) if str(x.get(key)) == subject_id), None)
            if item:
                geometry = item.get("geometry")
                break
    if not isinstance(geometry, dict) or not geometry.get("type") or "coordinates" not in geometry:
        raise GeometryPayloadError(f"cannot resolve governed geometry for {record.source_id}")
    expected = str(p.get("geometry_type_code", "")).upper()
    if str(geometry.get("type", "")).upper() != expected:
        raise GeometryPayloadError(f"geometry type mismatch for {record.source_id}: expected {expected}, got {geometry.get('type')}")
    return geometry

__all__ = ["GeometryPayloadError", "load_geometry"]
