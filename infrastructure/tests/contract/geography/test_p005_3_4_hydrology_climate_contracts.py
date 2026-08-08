from pathlib import Path
import json
from infrastructure.geography.hydrology import validate_hydrology_dataset
from infrastructure.geography.climate import validate_climate_dataset
ROOT=Path(__file__).resolve().parents[4]

def test_p005_3_4_contracts_preserve_locked_boundary_terrain_and_runtime_lineage():
    hyd=json.loads((ROOT/'data/novegeo/geography/hydrology/qualified/novegeo_hydrology_v001.json').read_text())
    climate=json.loads((ROOT/'data/novegeo/geography/climate/qualified/novegeo_climate_v001.json').read_text())
    validate_hydrology_dataset(hyd); validate_climate_dataset(climate)
    assert hyd['boundaryId']=='boundary:novegeo:sovereign' and hyd['boundaryVersion']==2
    assert hyd['terrainDatasetId']=='dataset:novegeo:terrain:elevation' and hyd['terrainDatasetVersion']==1
    assert climate['hydrologyDatasetId']==hyd['datasetId'] and climate['hydrologyDatasetVersion']==1
    assert hyd['runtimeMode']==climate['runtimeMode']=='shared_reference'
    assert climate['units']['rainfall']=='millimetre_per_year'
    assert climate['units']['windSpeed']=='metre_per_second'
