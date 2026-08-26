from dataclasses import replace
import pytest

from registries.nngla.spatial_realization.contracts import (
    CityRoot,FindingSeverity,FindingStatus,GeometryCandidate,GeometryEncoding,GeometryRole,
    SpatialRealizationExecutionReceipt,SubjectType,TargetSnapshot,TopologyFinding,
)


def test_city_root_and_geometry_identity_contracts_are_typed():
    root=CityRoot('NG-PLC-000001','NGP-000001','Orivane','NGR-01','NG-ADM-000009','NG-ADM-000001')
    assert root.administrative_area_id=='NG-ADM-000009'
    with pytest.raises(ValueError):CityRoot('Orivane','NGP-000001','Orivane','NGR-01','NG-ADM-000009','NG-ADM-000001')
    candidate=GeometryCandidate('NG-PLC-000001',SubjectType.PLACE,'NG-PLC-000001',GeometryRole.PLACE_REFERENCE_POINT,'placeref:x','POINT',GeometryEncoding.GEOJSON,'{"coordinates":[0,0],"type":"Point"}','0'*64,'key','dataset:x','1','source')
    assert candidate.is_source_successor is False


def test_target_snapshot_digest_is_deterministic():
    a=TargetSnapshot('db','env')
    b=TargetSnapshot('db','env')
    assert a.digest==b.digest and len(a.digest)==64


def test_finding_blocking_depends_on_open_status():
    f=TopologyFinding('finding:x','NG-PLC-000001','RULE',FindingSeverity.BLOCKING,FindingStatus.OPEN,'NG-ADM-000009')
    assert f.blocking
    assert not f.resolved().blocking


def test_execution_receipt_requires_actor_separation():
    with pytest.raises(ValueError):
        SpatialRealizationExecutionReceipt('nnglarun:spatial-realization:x','0'*64,'db','env','rev','same','same',1,0,0,0,'APPLIED',False)
