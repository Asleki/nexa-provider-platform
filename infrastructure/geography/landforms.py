"""P005.2 governed mountain, valley, plain and plateau semantic layer."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import math


class LandformValidationError(ValueError):
    """Raised when P005.2 landform authority violates its contract."""


CANONICAL_LANDFORM_CLASSES = frozenset({"mountain", "valley", "plain", "plateau"})


@dataclass(frozen=True, slots=True)
class LandformFeature:
    landform_id: str
    landform_class: str
    longitude: float
    latitude: float
    elevation_meters: int
    influence_radius_degrees: float

    def __post_init__(self) -> None:
        if not self.landform_id.startswith("landform:novegeo:"):
            raise LandformValidationError("landform identity must be namespaced")
        if self.landform_class not in CANONICAL_LANDFORM_CLASSES:
            raise LandformValidationError("unsupported landform class")
        if not all(math.isfinite(value) for value in (self.longitude, self.latitude, self.influence_radius_degrees)):
            raise LandformValidationError("landform coordinates/radius must be finite")
        if self.influence_radius_degrees <= 0:
            raise LandformValidationError("landform influence radius must be positive")


def load_landform_dataset(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LandformValidationError(f"cannot read landform dataset: {exc}") from exc
    if not isinstance(value, dict):
        raise LandformValidationError("landform dataset must be an object")
    return value


def validate_landform_dataset(value: dict[str, Any]) -> tuple[LandformFeature, ...]:
    if value.get("type") != "FeatureCollection":
        raise LandformValidationError("landform dataset must be a FeatureCollection")
    properties = value.get("properties")
    if not isinstance(properties, dict):
        raise LandformValidationError("landform dataset properties are required")
    required = {
        "datasetId": "dataset:novegeo:landforms",
        "datasetVersion": 1,
        "boundaryId": "boundary:novegeo:sovereign",
        "boundaryVersion": 2,
        "terrainDatasetId": "dataset:novegeo:terrain:elevation",
        "terrainDatasetVersion": 1,
        "runtimeMode": "shared_reference",
        "visibility": "public",
    }
    for key, expected in required.items():
        if properties.get(key) != expected:
            raise LandformValidationError(f"{key} expected {expected!r}, got {properties.get(key)!r}")
    if set(properties.get("canonicalClasses", [])) != CANONICAL_LANDFORM_CLASSES:
        raise LandformValidationError("canonical landform classes are incomplete")

    raw_features = value.get("features")
    if not isinstance(raw_features, list) or not raw_features:
        raise LandformValidationError("landform features are required")
    result = []
    for raw in raw_features:
        if not isinstance(raw, dict) or raw.get("type") != "Feature":
            raise LandformValidationError("each landform must be a Feature")
        props = raw.get("properties") or {}
        geometry = raw.get("geometry") or {}
        if geometry.get("type") != "Point":
            raise LandformValidationError("v001 landform authority uses Point feature anchors")
        coordinates = geometry.get("coordinates")
        if not isinstance(coordinates, list) or len(coordinates) != 2:
            raise LandformValidationError("landform point requires longitude and latitude")
        result.append(
            LandformFeature(
                landform_id=str(raw.get("id", "")),
                landform_class=str(props.get("landformClass", "")),
                longitude=float(coordinates[0]),
                latitude=float(coordinates[1]),
                elevation_meters=int(props.get("elevationMeters", 0)),
                influence_radius_degrees=float(props.get("influenceRadiusDegrees", 0)),
            )
        )
    if {item.landform_class for item in result} != CANONICAL_LANDFORM_CLASSES:
        raise LandformValidationError("published landforms must include all canonical classes")
    if len({item.landform_id for item in result}) != len(result):
        raise LandformValidationError("landform identities must be unique")
    return tuple(result)
