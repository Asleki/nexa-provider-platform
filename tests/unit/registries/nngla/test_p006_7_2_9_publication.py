from dataclasses import replace
import pytest

from registries.country.operating_context import RecordEffectScope
from registries.nngla.canonicalization import CanonicalizationService
from registries.nngla.ingest import IngestBatch, IngestState, StagedRecord
from registries.nngla.publication import (
    MemoryNNGLAPublicationRepository, NNGLAPublicationService,
    evaluate_publication_eligibility,
)
from registries.nngla.source_dataset import DataClassification, SourceRecordReference
from shared.runtime.operation_runtime import OperationRuntimeMode


def _receipt(*, dry_run=False, runtime=OperationRuntimeMode.SIMULATION):
    batch = IngestBatch.create(
        source_dataset_id="dataset:test:publication", source_dataset_version="1",
        runtime_mode=runtime, effect_scope=RecordEffectScope.RUNTIME_SCOPED,
        classification=DataClassification.PUBLIC_REFERENCE,
    )
    source = SourceRecordReference("dataset:test:publication", "1", "row:1", "test.csv", 1)
    staged = StagedRecord.create(batch=batch, source=source, record_family="ROAD_REFERENCE", candidate_id="cand:1", raw_payload={"road_id":"NG-RD-000001"})
    ready = replace(staged, state=IngestState.CANONICALIZATION_READY)
    return CanonicalizationService().canonicalize(ready, canonical_id="NG-RD-000001", dry_run=dry_run)


def test_public_and_public_reference_are_eligible_but_sensitive_is_not():
    receipt = _receipt()
    assert evaluate_publication_eligibility(receipt, classification=DataClassification.PUBLIC, record_family="ROAD_REFERENCE").eligible
    assert evaluate_publication_eligibility(receipt, classification=DataClassification.PUBLIC_REFERENCE, record_family="ROAD_REFERENCE").eligible
    blocked = evaluate_publication_eligibility(receipt, classification=DataClassification.SECURITY_SENSITIVE, record_family="ROAD_REFERENCE")
    assert not blocked.eligible
    assert "CLASSIFICATION_NOT_PUBLIC" in blocked.reasons


def test_dry_run_canonicalization_is_never_publishable():
    receipt = _receipt(dry_run=True)
    decision = evaluate_publication_eligibility(receipt, classification=DataClassification.PUBLIC, record_family="ROAD_REFERENCE")
    assert not decision.eligible
    assert "DRY_RUN_NOT_PUBLISHABLE" in decision.reasons


def test_publication_preserves_canonical_lineage_runtime_and_content_integrity():
    receipt = _receipt(runtime=OperationRuntimeMode.PRODUCTION)
    repo = MemoryNNGLAPublicationRepository()
    record = NNGLAPublicationService(repo).publish(
        receipt, record_family="ROAD_REFERENCE", classification=DataClassification.PUBLIC_REFERENCE,
        payload={"canonicalId":"NG-RD-000001"},
    )
    assert record.canonical_id == receipt.crosswalk.canonical_id
    assert record.canonicalization_receipt_id == receipt.receipt_id
    assert record.runtime_mode is OperationRuntimeMode.PRODUCTION
    assert record.visibility == "public"
    assert len(record.content_sha256) == 64
    assert repo.get(record.publication_id, 1) == record


def test_publication_repository_rejects_duplicate_publication_version():
    receipt = _receipt()
    repo = MemoryNNGLAPublicationRepository()
    service = NNGLAPublicationService(repo)
    record = service.publish(receipt, record_family="ROAD_REFERENCE", classification=DataClassification.PUBLIC)
    with pytest.raises(ValueError, match="already exists"):
        repo.add(record)
