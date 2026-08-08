"""P005.6 cross-layer environmental qualification."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .terrain import load_terrain_dataset,validate_terrain_dataset
from .landforms import load_landform_dataset,validate_landform_dataset
from .hydrology import load_hydrology_dataset,validate_hydrology_dataset
from .climate import load_climate_dataset,validate_climate_dataset
from .vegetation import load_vegetation_dataset,validate_vegetation_dataset

class EnvironmentQualificationError(ValueError): pass
@dataclass(frozen=True,slots=True)
class EnvironmentQualification:
    qualification_id:str; decision:str; boundary_version:int; layer_count:int; runtime_mode:str

def qualify_environment_stack(*,terrain_path:Path,landforms_path:Path,hydrology_path:Path,climate_path:Path,vegetation_path:Path)->EnvironmentQualification:
    terrain=load_terrain_dataset(terrain_path);validate_terrain_dataset(terrain)
    landforms=load_landform_dataset(landforms_path);validate_landform_dataset(landforms)
    hydrology=validate_hydrology_dataset(load_hydrology_dataset(hydrology_path))
    climate=validate_climate_dataset(load_climate_dataset(climate_path))
    vegetation=validate_vegetation_dataset(load_vegetation_dataset(vegetation_path))
    layers=[terrain,landforms.get("properties",{}),hydrology,climate,vegetation]
    if any(layer.get("boundaryVersion")!=2 for layer in layers):raise EnvironmentQualificationError("every P005 layer must retain boundary v002 lineage")
    if any(layer.get("runtimeMode")!="shared_reference" for layer in layers):raise EnvironmentQualificationError("every P005 layer must retain shared_reference runtime")
    if hydrology.get("terrainDatasetId")!=terrain.get("datasetId"):raise EnvironmentQualificationError("hydrology terrain lineage is broken")
    if climate.get("terrainDatasetId")!=terrain.get("datasetId") or climate.get("hydrologyDatasetId")!=hydrology.get("datasetId"):raise EnvironmentQualificationError("climate environmental lineage is broken")
    if vegetation.get("terrainDatasetId")!=terrain.get("datasetId") or vegetation.get("hydrologyDatasetId")!=hydrology.get("datasetId") or vegetation.get("climateDatasetId")!=climate.get("datasetId"):raise EnvironmentQualificationError("vegetation environmental lineage is broken")
    return EnvironmentQualification("qualification:novegeo:environment:p005:v001","qualified",2,5,"shared_reference")
