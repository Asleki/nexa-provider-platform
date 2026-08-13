"""P006.7.2.6 ingest, staging and quarantine foundation."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping
from uuid import uuid4
from shared.runtime.operation_runtime import OperationRuntimeMode
from registries.country.operating_context import RecordEffectScope
from .source_dataset import DataClassification, SourceRecordReference


class IngestState(str, Enum):
    RECEIVED = "RECEIVED"
    STAGED = "STAGED"
    VALIDATED = "VALIDATED"
    QUARANTINED = "QUARANTINED"
    REJECTED = "REJECTED"
    CANONICALIZATION_READY = "CANONICALIZATION_READY"
    CANONICALIZED = "CANONICALIZED"


class QuarantineCode(str, Enum):
    INVALID_SCHEMA = "INVALID_SCHEMA"
    INVALID_IDENTIFIER = "INVALID_IDENTIFIER"
    INVALID_REFERENCE = "INVALID_REFERENCE"
    INVALID_RUNTIME = "INVALID_RUNTIME"
    INVALID_EFFECT_SCOPE = "INVALID_EFFECT_SCOPE"
    INVALID_CRS = "INVALID_CRS"
    INVALID_GEOMETRY = "INVALID_GEOMETRY"
    HASH_MISMATCH = "HASH_MISMATCH"
    DUPLICATE_SOURCE_RECORD = "DUPLICATE_SOURCE_RECORD"
    DUPLICATE_CANONICAL_ID = "DUPLICATE_CANONICAL_ID"
    MISSING_PROVENANCE = "MISSING_PROVENANCE"


def _freeze(mapping: Mapping[str, object]) -> Mapping[str, object]:
    if not isinstance(mapping, Mapping):
        raise TypeError("payload must be a mapping")
    return MappingProxyType(dict(mapping))


@dataclass(frozen=True, slots=True)
class IngestBatch:
    ingest_batch_id: str
    source_dataset_id: str
    source_dataset_version: str
    runtime_mode: OperationRuntimeMode
    effect_scope: RecordEffectScope
    classification: DataClassification
    received_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.ingest_batch_id.startswith("ingest:nngla:"):
            raise ValueError("ingest_batch_id must use ingest:nngla: namespace")
        if not self.source_dataset_id.startswith("dataset:"):
            raise ValueError("source_dataset_id must use dataset: namespace")
        object.__setattr__(self, "runtime_mode", OperationRuntimeMode.parse(self.runtime_mode))
        if not isinstance(self.effect_scope, RecordEffectScope):
            object.__setattr__(self, "effect_scope", RecordEffectScope(str(self.effect_scope)))
        if self.effect_scope is RecordEffectScope.SIMULATION_ONLY and self.runtime_mode is not OperationRuntimeMode.SIMULATION:
            raise ValueError("SIMULATION_ONLY effect requires simulation runtime")
        if self.effect_scope is RecordEffectScope.PRODUCTION_ONLY and self.runtime_mode is not OperationRuntimeMode.PRODUCTION:
            raise ValueError("PRODUCTION_ONLY effect requires production runtime")
        if self.received_at.tzinfo is None or self.received_at.utcoffset() is None:
            raise ValueError("received_at must be timezone-aware")

    @classmethod
    def create(cls, *, source_dataset_id: str, source_dataset_version: str, runtime_mode, effect_scope, classification):
        return cls(f"ingest:nngla:{uuid4()}", source_dataset_id, source_dataset_version, runtime_mode, effect_scope, classification)


@dataclass(frozen=True, slots=True)
class StagedRecord:
    staged_record_id: str
    batch: IngestBatch
    source: SourceRecordReference
    record_family: str
    candidate_id: str
    raw_payload: Mapping[str, object]
    state: IngestState = IngestState.STAGED
    staged_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.staged_record_id.startswith("staged:nngla:"):
            raise ValueError("staged_record_id must use staged:nngla: namespace")
        if self.source.dataset_id != self.batch.source_dataset_id or self.source.dataset_version != self.batch.source_dataset_version:
            raise ValueError("source record must belong to the ingest batch dataset/version")
        if self.state not in {IngestState.STAGED, IngestState.VALIDATED, IngestState.CANONICALIZATION_READY}:
            raise ValueError("staged record cannot start in a terminal/quarantine state")
        if not self.record_family or not self.candidate_id:
            raise ValueError("record_family and candidate_id are required")
        object.__setattr__(self, "raw_payload", _freeze(self.raw_payload))
        if self.staged_at.tzinfo is None or self.staged_at.utcoffset() is None:
            raise ValueError("staged_at must be timezone-aware")

    @classmethod
    def create(cls, *, batch: IngestBatch, source: SourceRecordReference, record_family: str, candidate_id: str, raw_payload: Mapping[str, object]):
        return cls(f"staged:nngla:{uuid4()}", batch, source, record_family, candidate_id, raw_payload)


@dataclass(frozen=True, slots=True)
class QuarantineRecord:
    quarantine_id: str
    staged_record_id: str
    source: SourceRecordReference
    error_code: QuarantineCode
    error_message: str
    raw_payload: Mapping[str, object]
    quarantined_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.quarantine_id.startswith("quarantine:nngla:"):
            raise ValueError("quarantine_id must use quarantine:nngla: namespace")
        if not self.staged_record_id.startswith("staged:nngla:"):
            raise ValueError("staged_record_id must reference a staged NNGLA record")
        if not self.error_message.strip():
            raise ValueError("error_message is required")
        object.__setattr__(self, "raw_payload", _freeze(self.raw_payload))

    @classmethod
    def from_staged(cls, staged: StagedRecord, *, error_code: QuarantineCode, error_message: str):
        return cls(f"quarantine:nngla:{uuid4()}", staged.staged_record_id, staged.source, error_code, error_message, staged.raw_payload)


class MemoryIngestStore:
    def __init__(self) -> None:
        self._staged: dict[str, StagedRecord] = {}
        self._quarantine: dict[str, QuarantineRecord] = {}
        self._source_keys: set[tuple[str, str, str, str]] = set()

    def stage(self, record: StagedRecord) -> StagedRecord:
        key = (record.source.dataset_id, record.source.dataset_version, record.source.source_record_id, record.batch.runtime_mode.value)
        if key in self._source_keys:
            raise ValueError("source record already staged for this runtime")
        self._source_keys.add(key)
        self._staged[record.staged_record_id] = record
        return record

    def quarantine(self, record: QuarantineRecord) -> QuarantineRecord:
        if record.staged_record_id not in self._staged:
            raise KeyError(record.staged_record_id)
        self._quarantine[record.quarantine_id] = record
        return record

    def staged_records(self) -> tuple[StagedRecord, ...]:
        return tuple(self._staged[k] for k in sorted(self._staged))

    def quarantine_records(self) -> tuple[QuarantineRecord, ...]:
        return tuple(self._quarantine[k] for k in sorted(self._quarantine))


__all__ = [
    "IngestState", "QuarantineCode", "IngestBatch", "StagedRecord", "QuarantineRecord", "MemoryIngestStore",
]
