from pathlib import Path
import pytest
from infrastructure.geography.vegetation import load_vegetation_dataset,validate_vegetation_dataset,qualify_vegetation_dataset,VegetationValidationError
ROOT=Path(__file__).resolve().parents[4]
DATA=ROOT/'data/novegeo/geography/vegetation/qualified/novegeo_vegetation_v001.json'
def test_p005_5_vegetation_is_governed_anonymous_and_referenceable():
    v=validate_vegetation_dataset(load_vegetation_dataset(DATA));assert v['boundaryVersion']==2;assert v['runtimeMode']=='shared_reference';assert len(v['samples'])>=200
    assert all(s['vegetationCellId'].startswith('vegetation:novegeo:cell:') and 'name' not in s for s in v['samples'])
def test_p005_5_qualification_passes():
    q=qualify_vegetation_dataset(DATA);assert q.decision=='qualified';assert q.sample_count>=200
def test_p005_5_rejects_replacement_climate_lineage():
    v=load_vegetation_dataset(DATA);v['climateDatasetId']='dataset:wrong'
    with pytest.raises(VegetationValidationError):validate_vegetation_dataset(v)
