from pathlib import Path
import json
from infrastructure.geography.hydrology import qualify_hydrology_dataset
from infrastructure.geography.climate import qualify_climate_dataset
ROOT=Path(__file__).resolve().parents[4]

def test_p005_3_4_publication_pipeline_is_qualified_browser_safe_and_additive():
    hr=qualify_hydrology_dataset(ROOT/'data/novegeo/geography/hydrology/qualified/novegeo_hydrology_v001.json')
    cr=qualify_climate_dataset(ROOT/'data/novegeo/geography/climate/qualified/novegeo_climate_v001.json')
    hm=json.loads((ROOT/'data/novegeo/geography/hydrology/publication/v001/publication-manifest.json').read_text())
    cm=json.loads((ROOT/'data/novegeo/geography/climate/publication/v001/publication-manifest.json').read_text())
    bh=json.loads((ROOT/'frontend/public/geography/novegeo/hydrology/v001/standard.json').read_text())
    bc=json.loads((ROOT/'frontend/public/geography/novegeo/climate/v001/standard.json').read_text())
    assert hr.decision==cr.decision=='qualified'
    assert hm['activation']=={'active':True,'activatedByMilestone':'P005.3'}
    assert cm['activation']=={'active':True,'activatedByMilestone':'P005.4'}
    assert bh['contentSha256']==hm['sourceContentSha256']
    assert bc['contentSha256']==cm['sourceContentSha256']
    assert len(bh['rivers'])==5 and len(bh['lakes'])==3
    assert len(bc['rainfallSystems'])==2
