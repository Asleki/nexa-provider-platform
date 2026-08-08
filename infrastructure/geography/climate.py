"""P005.4 governed climate, rainfall and wind baseline."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json, math
from .geometry import canonical_sha256

class ClimateValidationError(ValueError): pass

@dataclass(frozen=True, slots=True)
class ClimateQualification:
    qualification_id: str
    decision: str
    sample_count: int
    rainfall_system_count: int
    content_sha256: str

def load_climate_dataset(path: Path) -> dict[str, Any]:
    try: value=json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc: raise ClimateValidationError(f"cannot read climate dataset: {exc}") from exc
    if not isinstance(value,dict): raise ClimateValidationError("climate dataset must be an object")
    return value

def validate_climate_dataset(value: dict[str, Any]) -> dict[str, Any]:
    required={"climateId":"climate:novegeo:baseline","climateVersion":1,"datasetId":"dataset:novegeo:climate:baseline","datasetVersion":1,"boundaryId":"boundary:novegeo:sovereign","boundaryVersion":2,"terrainDatasetId":"dataset:novegeo:terrain:elevation","terrainDatasetVersion":1,"hydrologyDatasetId":"dataset:novegeo:hydrology:surface-water","hydrologyDatasetVersion":1,"runtimeMode":"shared_reference","visibility":"public"}
    for k,e in required.items():
        if value.get(k)!=e: raise ClimateValidationError(f"{k} expected {e!r}, got {value.get(k)!r}")
    units=value.get("units",{})
    expected_units={"temperature":"degree_celsius","rainfall":"millimetre_per_year","windSpeed":"metre_per_second","windDirection":"degree_clockwise_from_north"}
    if units!=expected_units: raise ClimateValidationError("climate units must remain explicit and governed")
    if value.get("cartographicModel",{}).get("featureNamingAuthority")!="deferred": raise ClimateValidationError("atmospheric feature naming must remain deferred")
    systems=value.get("rainfallSystems")
    if not isinstance(systems,list) or len(systems)!=2: raise ClimateValidationError("P005.4 requires exactly two governed rainfall systems")
    ids=set()
    for s in systems:
        sid=s.get("rainfallSystemId")
        if not isinstance(sid,str) or not sid.startswith("rainfall:novegeo:rs") or sid in ids: raise ClimateValidationError("rainfall system IDs must be anonymous, unique and namespaced")
        if "name" in s: raise ClimateValidationError("rainfall system names are deferred")
        ids.add(sid)
        rp=s.get("referencePoint",{})
        if not all(isinstance(rp.get(k),(int,float)) and math.isfinite(rp.get(k)) for k in ("longitude","latitude")): raise ClimateValidationError("rainfall referencePoint is invalid")
        fm=s.get("fieldModel",{})
        if fm.get("type")!="irregular_radial_intensity" or fm.get("visibleBoundary") is not False: raise ClimateValidationError("rainfall must use an irregular invisible-boundary field model")
    by_power=sorted(systems,key=lambda s:float(s.get("relativePower",0)))
    weaker,stronger=by_power
    if weaker.get("intensityClass")!="strong" or stronger.get("intensityClass")!="powerful": raise ClimateValidationError("rainfall systems must distinguish strong and powerful intensity")
    if stronger["peakAnnualRainfallMm"]<=weaker["peakAnnualRainfallMm"]: raise ClimateValidationError("powerful rainfall must exceed strong rainfall peak")
    weak_area=weaker["radiusLongitudeDegrees"]*weaker["radiusLatitudeDegrees"]
    strong_area=stronger["radiusLongitudeDegrees"]*stronger["radiusLatitudeDegrees"]
    if strong_area<=weak_area: raise ClimateValidationError("powerful rainfall system must also be geographically larger")
    samples=value.get("samples")
    if not isinstance(samples,list) or len(samples)<200: raise ClimateValidationError("climate baseline requires broad governed sampling")
    for s in samples:
        vals=[s.get("longitude"),s.get("latitude"),s.get("annualRainfallMm"),s.get("meanTemperatureC"),s.get("meanWindSpeedMps"),s.get("prevailingWindDirectionDegrees")]
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in vals): raise ClimateValidationError("climate sample values must be finite")
        if s["annualRainfallMm"]<0 or s["meanWindSpeedMps"]<0 or not 0<=s["prevailingWindDirectionDegrees"]<360: raise ClimateValidationError("climate sample range invalid")
    expected=value.get("contentSha256"); unsigned=dict(value); unsigned.pop("contentSha256",None)
    if not isinstance(expected,str) or canonical_sha256(unsigned)!=expected: raise ClimateValidationError("climate contentSha256 mismatch")
    return value

def qualify_climate_dataset(path: Path) -> ClimateQualification:
    value=validate_climate_dataset(load_climate_dataset(path))
    return ClimateQualification("qualification:novegeo:climate:v001","qualified",len(value["samples"]),len(value["rainfallSystems"]),value["contentSha256"])
