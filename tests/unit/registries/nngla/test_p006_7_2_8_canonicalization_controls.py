from dataclasses import replace
from registries.nngla.canonicalization import CanonicalizationService
from registries.nngla.ingest import IngestBatch,StagedRecord,IngestState
from registries.nngla.source_dataset import SourceRecordReference,DataClassification
from registries.country.operating_context import RecordEffectScope
from shared.runtime.operation_runtime import OperationRuntimeMode


def _record(runtime=OperationRuntimeMode.SIMULATION,source_id="SRC-1"):
    batch=IngestBatch.create(source_dataset_id="dataset:novegeo:test",source_dataset_version="1",runtime_mode=runtime,effect_scope=RecordEffectScope.RUNTIME_SCOPED,classification=DataClassification.INTERNAL)
    source=SourceRecordReference("dataset:novegeo:test","1",source_id,"x.csv",1)
    return StagedRecord.create(batch=batch,source=source,record_family="ROAD_REFERENCE",candidate_id="NG-RD-CAND-1",raw_payload={"road_name":"A"})


def test_canonicalization_requires_validated_record_and_is_idempotent():
    svc=CanonicalizationService(); staged=_record()
    try: svc.canonicalize(staged,canonical_id="NG-RD-000001")
    except ValueError: pass
    else: raise AssertionError("unvalidated candidate canonicalized")
    ready=replace(staged,state=IngestState.CANONICALIZATION_READY)
    a=svc.canonicalize(ready,canonical_id="NG-RD-000001",validation_references=("VAL-1",))
    b=svc.canonicalize(ready,canonical_id="NG-RD-000001",validation_references=("VAL-1",))
    assert a is b and len(svc.receipts())==1


def test_dry_run_does_not_reserve_or_persist_crosswalk():
    svc=CanonicalizationService(); ready=replace(_record(),state=IngestState.VALIDATED)
    receipt=svc.canonicalize(ready,canonical_id="NG-RD-000001",dry_run=True)
    assert receipt.dry_run and svc.receipts()==()
    assert svc.canonicalize(ready,canonical_id="NG-RD-000001").dry_run is False


def test_same_canonical_id_can_remain_runtime_distinguishable():
    svc=CanonicalizationService()
    sim=replace(_record(OperationRuntimeMode.SIMULATION,"SRC-SIM"),state=IngestState.VALIDATED)
    prod=replace(_record(OperationRuntimeMode.PRODUCTION,"SRC-PROD"),state=IngestState.VALIDATED)
    svc.canonicalize(sim,canonical_id="NG-RD-000001")
    svc.canonicalize(prod,canonical_id="NG-RD-000001")
    assert len(svc.receipts())==2
