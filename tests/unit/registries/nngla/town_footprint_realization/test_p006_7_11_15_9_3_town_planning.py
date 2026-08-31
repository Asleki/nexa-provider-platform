from registries.nngla.town_footprint_realization.contracts import TownIdentity,TownSourceEvidence,SOURCE_BASIS,SOURCE_QUALIFICATION_STATUS,LEGAL_BOUNDARY_STATUS
from registries.nngla.town_footprint_realization.planning import qualify_source

def test_multi_artifact_parentage_guard():
    source=TownSourceEvidence("NG-PLC-000001","Town","NGR-01","NGP-000001","NGP-000002","SETTLEMENT_FOOTPRINT",LEGAL_BOUNDARY_STATUS,SOURCE_QUALIFICATION_STATUS,SOURCE_BASIS,"dataset:novegeo:place-spatial-association","1","SHARED_REFERENCE","paths","0"*64,"1"*64,"2"*64,"3"*64,"POLYGON",{})
    identity=TownIdentity("NG-PLC-000001","Town","NGR-01","NGP-000001","NGP-000002","NG-PLC-000002","MUNICIPALITY","NG-ADM-000002","municipality-geometry:nngla:NG-ADM-000002:v1","4"*64)
    assert qualify_source(source,identity)
