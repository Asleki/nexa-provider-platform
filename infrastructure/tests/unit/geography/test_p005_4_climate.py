from pathlib import Path
import json
import pytest
from infrastructure.geography.climate import validate_climate_dataset, qualify_climate_dataset, ClimateValidationError
ROOT=Path(__file__).resolve().parents[4]
PATH=ROOT/'data/novegeo/geography/climate/qualified/novegeo_climate_v001.json'

def test_p005_4_climate_has_two_distinct_rainfall_systems_and_explicit_units():
    value=json.loads(PATH.read_text())
    validate_climate_dataset(value)
    receipt=qualify_climate_dataset(PATH)
    assert receipt.decision=='qualified'
    assert receipt.rainfall_system_count==2
    assert receipt.sample_count>=250
    systems=sorted(value['rainfallSystems'],key=lambda s:s['relativePower'])
    assert systems[0]['intensityClass']=='strong'
    assert systems[1]['intensityClass']=='powerful'
    assert systems[1]['peakAnnualRainfallMm']>systems[0]['peakAnnualRainfallMm']
    assert systems[1]['radiusLongitudeDegrees']*systems[1]['radiusLatitudeDegrees'] > systems[0]['radiusLongitudeDegrees']*systems[0]['radiusLatitudeDegrees']

def test_p005_4_rejects_climate_without_stronger_powerful_rainfall():
    value=json.loads(PATH.read_text())
    value['rainfallSystems'][1]['peakAnnualRainfallMm']=1000
    with pytest.raises(ClimateValidationError,match='powerful rainfall'):
        validate_climate_dataset(value)
