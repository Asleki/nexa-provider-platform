"""P005.5 governed vegetation and arid-zone baseline."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json, math
from .geometry import canonical_sha256

VEGETATION_CLASSES=frozenset({"dense_vegetation","woodland","grassland","sparse_vegetation","arid_surface"})
ARIDITY_CLASSES=frozenset({"arid","semi_arid","non_arid"})
class VegetationValidationError(ValueError): pass

@dataclass(frozen=True,slots=True)
class VegetationQualification:
    qualification_id:str; decision:str; sample_count:int; content_sha256:str

def load_vegetation_dataset(path:Path)->dict[str,Any]:
    try:value=json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as exc:raise VegetationValidationError(f"cannot read vegetation dataset: {exc}") from exc
    if not isinstance(value,dict):raise VegetationValidationError("vegetation dataset must be an object")
    return value

def validate_vegetation_dataset(value:dict[str,Any])->dict[str,Any]:
    required={"biosphereId":"biosphere:novegeo:vegetation-baseline","biosphereVersion":1,"datasetId":"dataset:novegeo:vegetation:baseline","datasetVersion":1,"boundaryId":"boundary:novegeo:sovereign","boundaryVersion":2,"terrainDatasetId":"dataset:novegeo:terrain:elevation","terrainDatasetVersion":1,"hydrologyDatasetId":"dataset:novegeo:hydrology:surface-water","hydrologyDatasetVersion":1,"climateDatasetId":"dataset:novegeo:climate:baseline","climateDatasetVersion":1,"runtimeMode":"shared_reference","visibility":"public"}
    for k,e in required.items():
        if value.get(k)!=e:raise VegetationValidationError(f"{k} expected {e!r}, got {value.get(k)!r}")
    if value.get("coordinateReference",{}).get("coordinateReferenceId")!="crs:novegeo:geographic":raise VegetationValidationError("vegetation CRS lineage is invalid")
    classification=value.get("classification",{})
    if set(classification.get("vegetationClasses",[]))!=VEGETATION_CLASSES:raise VegetationValidationError("vegetation classes are incomplete")
    if set(classification.get("aridityClasses",[]))!=ARIDITY_CLASSES:raise VegetationValidationError("aridity classes are incomplete")
    if classification.get("namingAuthority")!="deferred":raise VegetationValidationError("vegetation naming authority must remain deferred")
    samples=value.get("samples")
    if not isinstance(samples,list) or len(samples)<200:raise VegetationValidationError("vegetation baseline requires broad governed sampling")
    ids=set(); coords=set(); present_v=set(); present_a=set()
    for s in samples:
        sid=s.get("vegetationCellId")
        if not isinstance(sid,str) or not sid.startswith("vegetation:novegeo:cell:") or sid in ids:raise VegetationValidationError("vegetation cell IDs must be stable, anonymous and unique")
        ids.add(sid)
        if "name" in s:raise VegetationValidationError("vegetation feature naming is deferred")
        lon,lat=s.get("longitude"),s.get("latitude")
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (lon,lat)):raise VegetationValidationError("vegetation coordinates must be finite")
        coord=(float(lon),float(lat))
        if coord in coords:raise VegetationValidationError("vegetation cell coordinates must be unique")
        coords.add(coord)
        vc,ac=s.get("vegetationClass"),s.get("aridityClass")
        if vc not in VEGETATION_CLASSES or ac not in ARIDITY_CLASSES:raise VegetationValidationError("vegetation/aridity classification is invalid")
        present_v.add(vc);present_a.add(ac)
        if not isinstance(s.get("sourceAnnualRainfallMm"),(int,float)) or s["sourceAnnualRainfallMm"]<0:raise VegetationValidationError("source rainfall must be non-negative")
        if not isinstance(s.get("sourceMeanTemperatureC"),(int,float)):raise VegetationValidationError("source temperature must be numeric")
    if present_v!=VEGETATION_CLASSES or present_a!=ARIDITY_CLASSES:raise VegetationValidationError("all governed vegetation/aridity classes must be represented")
    expected=value.get("contentSha256");unsigned=dict(value);unsigned.pop("contentSha256",None)
    if not isinstance(expected,str) or canonical_sha256(unsigned)!=expected:raise VegetationValidationError("vegetation contentSha256 mismatch")
    return value

def qualify_vegetation_dataset(path:Path)->VegetationQualification:
    value=validate_vegetation_dataset(load_vegetation_dataset(path))
    return VegetationQualification("qualification:novegeo:vegetation:v001","qualified",len(value["samples"]),value["contentSha256"])
