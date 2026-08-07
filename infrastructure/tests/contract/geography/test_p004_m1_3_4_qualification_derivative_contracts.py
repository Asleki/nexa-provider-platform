import json
from pathlib import Path
ROOT=Path(__file__).parents[4]; BOUNDARY_ROOT=ROOT/'data/novegeo/geography/world-boundary'

def test_qualification_and_derivative_contracts_separate_authority_from_publication():
    q=json.loads((BOUNDARY_ROOT/'contracts/sovereign-boundary-qualification-v001.json').read_text())
    d=json.loads((BOUNDARY_ROOT/'contracts/public-boundary-derivative-v001.json').read_text())
    assert q['activationPolicy']['qualificationDoesNotImplyRuntimePublication'] is True
    assert q['activationPolicy']['runtimeActivationDeferredTo']=='P004.M1.5'
    assert d['sourceMustBeQualified'] is True
    assert d['preservationPolicy']['offshoreIslandCountMustRemainStable'] is True
    assert d['runtimePublicationDeferredTo']=='P004.M1.5'

def test_materialized_10b_receipts_have_explicit_lineage_and_fingerprints():
    q=json.loads((BOUNDARY_ROOT/'qualification/novegeo_world_boundary_v002_qualification.json').read_text())
    s=json.loads((BOUNDARY_ROOT/'supersession/novegeo_world_boundary_v001_to_v002.json').read_text())
    assert q['boundaryVersion']==2 and q['supersedesBoundaryVersion']==1 and q['decision']=='qualified'
    assert len(q['receiptSha256'])==64
    assert s['predecessorVersion']==1 and s['successorVersion']==2
    assert s['qualificationReceiptSha256']==q['receiptSha256']
    assert s['runtimeActivationDeferredTo']=='P004.M1.5'
