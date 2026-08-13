from registries.nngla.ingest import *
from registries.nngla.source_dataset import *
from registries.country.operating_context import RecordEffectScope
from shared.runtime.operation_runtime import OperationRuntimeMode


def _source(): return SourceRecordReference("dataset:novegeo:test","1","SRC-1","x.csv",2)
def _batch(runtime=OperationRuntimeMode.SIMULATION,effect=RecordEffectScope.RUNTIME_SCOPED):
    return IngestBatch.create(source_dataset_id="dataset:novegeo:test",source_dataset_version="1",runtime_mode=runtime,effect_scope=effect,classification=DataClassification.INTERNAL)


def test_staging_keeps_raw_payload_and_source_lineage():
    batch=_batch(); staged=StagedRecord.create(batch=batch,source=_source(),record_family="GEOGRAPHIC_FEATURE",candidate_id="NG-FEAT-1",raw_payload={"name":"X"})
    store=MemoryIngestStore(); store.stage(staged)
    assert store.staged_records()==(staged,)
    assert staged.raw_payload["name"]=="X"
    try: staged.raw_payload["name"]="Y"
    except TypeError: pass
    else: raise AssertionError("raw payload is mutable")


def test_quarantine_preserves_failed_candidate_instead_of_deleting_it():
    staged=StagedRecord.create(batch=_batch(),source=_source(),record_family="GEOMETRY",candidate_id="NG-GEO-1",raw_payload={"crs":"BAD"})
    store=MemoryIngestStore(); store.stage(staged)
    q=QuarantineRecord.from_staged(staged,error_code=QuarantineCode.INVALID_CRS,error_message="unknown CRS")
    store.quarantine(q)
    assert store.staged_records()[0].candidate_id=="NG-GEO-1"
    assert store.quarantine_records()[0].error_code is QuarantineCode.INVALID_CRS


def test_runtime_effect_mismatch_is_rejected():
    try: _batch(OperationRuntimeMode.PRODUCTION,RecordEffectScope.SIMULATION_ONLY)
    except ValueError: pass
    else: raise AssertionError("cross-runtime effect was accepted")
