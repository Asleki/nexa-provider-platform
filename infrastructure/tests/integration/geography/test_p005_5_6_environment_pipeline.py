from pathlib import Path
from infrastructure.geography.environment import qualify_environment_stack
ROOT=Path(__file__).resolve().parents[4]
def test_p005_1_through_p005_5_form_one_qualified_environment_stack():
    q=qualify_environment_stack(
      terrain_path=ROOT/'data/novegeo/geography/terrain/qualified/novegeo_terrain_v001.json',
      landforms_path=ROOT/'data/novegeo/geography/landforms/qualified/novegeo_landforms_v001.geojson',
      hydrology_path=ROOT/'data/novegeo/geography/hydrology/qualified/novegeo_hydrology_v001.json',
      climate_path=ROOT/'data/novegeo/geography/climate/qualified/novegeo_climate_v001.json',
      vegetation_path=ROOT/'data/novegeo/geography/vegetation/qualified/novegeo_vegetation_v001.json')
    assert q.decision=='qualified';assert q.layer_count==5;assert q.boundary_version==2;assert q.runtime_mode=='shared_reference'
