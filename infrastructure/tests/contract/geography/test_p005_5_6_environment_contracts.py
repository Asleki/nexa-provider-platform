from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[4]
def test_p005_5_publication_manifest_and_contract_are_stable():
    manifest=json.loads((ROOT/'data/novegeo/geography/vegetation/publication/v001/publication-manifest.json').read_text())
    contract=json.loads((ROOT/'data/novegeo/geography/vegetation/contracts/vegetation-baseline-v001.json').read_text())
    assert manifest['datasetId']=='dataset:novegeo:vegetation:baseline';assert manifest['boundaryVersion']==2
    assert contract['namingAuthority']=='deferred';assert contract['requiredLineage']==['boundary','terrain','hydrology','climate']
def test_p005_5_browser_publication_matches_authoritative_hash():
    q=json.loads((ROOT/'data/novegeo/geography/vegetation/qualified/novegeo_vegetation_v001.json').read_text())
    p=json.loads((ROOT/'frontend/public/geography/novegeo/vegetation/v001/standard.json').read_text())
    assert p['contentSha256']==q['contentSha256'];assert p['datasetId']==q['datasetId']
