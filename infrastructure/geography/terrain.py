"""P005.1 governed terrain and elevation contracts and qualification helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import math

from .geometry import canonical_sha256


class TerrainValidationError(ValueError):
    """Raised when governed terrain/elevation data violates P005.1 contracts."""


@dataclass(frozen=True, slots=True)
class ElevationDatum:
    elevation_datum_id: str = "datum:novegeo:elevation:mean-sea-level"
    version: int = 1
    unit: str = "metre"
    zero_reference: str = "governed_novegeo_mean_sea_level"
    positive_direction: str = "up"

    def __post_init__(self) -> None:
        if not self.elevation_datum_id.startswith("datum:novegeo:elevation:"):
            raise TerrainValidationError("elevation datum must use the NoveGeo elevation namespace")
        if self.version < 1:
            raise TerrainValidationError("elevation datum version must be positive")
        if self.unit != "metre":
            raise TerrainValidationError("P005.1 elevation unit must be metre")
        if self.positive_direction != "up":
            raise TerrainValidationError("elevation positive direction must be up")


@dataclass(frozen=True, slots=True)
class TerrainSample:
    longitude: float
    latitude: float
    elevation_meters: int
    landform_class: str

    def __post_init__(self) -> None:
        if not math.isfinite(self.longitude) or not -180 <= self.longitude <= 180:
            raise TerrainValidationError("terrain longitude must be finite and valid")
        if not math.isfinite(self.latitude) or not -90 <= self.latitude <= 90:
            raise TerrainValidationError("terrain latitude must be finite and valid")
        if not isinstance(self.elevation_meters, int):
            raise TerrainValidationError("terrain elevation must be an integer number of metres")
        if self.landform_class not in {"mountain", "valley", "plain", "plateau"}:
            raise TerrainValidationError("unsupported terrain landform classification")


@dataclass(frozen=True, slots=True)
class TerrainQualification:
    qualification_id: str
    decision: str
    sample_count: int
    min_elevation_meters: int
    max_elevation_meters: int
    content_sha256: str


def load_terrain_dataset(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise TerrainValidationError(f"cannot read terrain dataset: {exc}") from exc
    if not isinstance(value, dict):
        raise TerrainValidationError("terrain dataset must be a JSON object")
    return value


def validate_terrain_dataset(value: dict[str, Any]) -> tuple[TerrainSample, ...]:
    required = {
        "terrainId": "terrain:novegeo:surface",
        "terrainVersion": 1,
        "datasetId": "dataset:novegeo:terrain:elevation",
        "datasetVersion": 1,
        "boundaryId": "boundary:novegeo:sovereign",
        "boundaryVersion": 2,
        "runtimeMode": "shared_reference",
        "visibility": "public",
    }
    for key, expected in required.items():
        if value.get(key) != expected:
            raise TerrainValidationError(f"{key} expected {expected!r}, got {value.get(key)!r}")

    crs = value.get("coordinateReference")
    if not isinstance(crs, dict) or crs.get("coordinateReferenceId") != "crs:novegeo:geographic":
        raise TerrainValidationError("terrain must reference governed NoveGeo geographic CRS")
    if crs.get("axisOrder") != ["longitude", "latitude"]:
        raise TerrainValidationError("terrain coordinate order must remain longitude, latitude")

    datum_value = value.get("elevationDatum")
    if not isinstance(datum_value, dict):
        raise TerrainValidationError("terrain elevation datum is required")
    ElevationDatum(
        elevation_datum_id=str(datum_value.get("elevationDatumId", "")),
        version=int(datum_value.get("version", 0)),
        unit=str(datum_value.get("unit", "")),
        zero_reference=str(datum_value.get("zeroReference", "")),
        positive_direction=str(datum_value.get("positiveDirection", "")),
    )

    sampling = value.get("sampling")
    if not isinstance(sampling, dict) or sampling.get("noDataValue", "missing") is not None:
        raise TerrainValidationError("terrain no-data value must be explicit null, never elevation zero")
    if sampling.get("landOnly") is not True:
        raise TerrainValidationError("P005.1 terrain authority is land-only; bathymetry is deferred")

    raw_samples = value.get("samples")
    if not isinstance(raw_samples, list) or not raw_samples:
        raise TerrainValidationError("terrain samples are required")

    samples = tuple(
        TerrainSample(
            longitude=float(item["longitude"]),
            latitude=float(item["latitude"]),
            elevation_meters=int(item["elevationMeters"]),
            landform_class=str(item["landformClass"]),
        )
        for item in raw_samples
    )
    if len({(sample.longitude, sample.latitude) for sample in samples}) != len(samples):
        raise TerrainValidationError("terrain sample coordinates must be unique")
    classes = {sample.landform_class for sample in samples}
    if classes != {"mountain", "valley", "plain", "plateau"}:
        raise TerrainValidationError("all four canonical P005.2 landform classes must be expressible")

    expected_hash = value.get("contentSha256")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise TerrainValidationError("terrain contentSha256 is required")
    unsigned = dict(value)
    unsigned.pop("contentSha256", None)
    if canonical_sha256(unsigned) != expected_hash:
        raise TerrainValidationError("terrain contentSha256 does not match deterministic content")
    return samples


def qualify_terrain_dataset(path: Path) -> TerrainQualification:
    value = load_terrain_dataset(path)
    samples = validate_terrain_dataset(value)
    elevations = [sample.elevation_meters for sample in samples]
    return TerrainQualification(
        qualification_id="qualification:novegeo:terrain:v001",
        decision="qualified",
        sample_count=len(samples),
        min_elevation_meters=min(elevations),
        max_elevation_meters=max(elevations),
        content_sha256=str(value["contentSha256"]),
    )


def sample_elevation(value: dict[str, Any], longitude: float, latitude: float) -> TerrainSample:
    """Return the nearest governed terrain sample for downstream read-only geography consumers."""
    samples = validate_terrain_dataset(value)
    if not math.isfinite(longitude) or not math.isfinite(latitude):
        raise TerrainValidationError("query coordinate must be finite")
    return min(samples, key=lambda sample: (sample.longitude - longitude) ** 2 + (sample.latitude - latitude) ** 2)
