"""P006.7.2.8 deterministic NNGLA migration/canonicalization controls."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from types import MappingProxyType
from collections.abc import Mapping
from uuid import uuid4
from shared.runtime.operation_runtime import OperationRuntimeMode
from registries.country.operating_context import RecordEffectScope
from .ingest import StagedRecord, IngestState


@dataclass(frozen=True, slots=True)
class CanonicalizationKey:
    dataset_id: str
    dataset_version: str
    source_record_id: str
    runtime_mode: OperationRuntimeMode
    effect_scope: RecordEffectScope

    def __post_init__(self) -> None:
        object.__setattr__(self, "runtime_mode", OperationRuntimeMode.parse(self.runtime_mode))
        if not isinstance(self.effect_scope, RecordEffectScope):
            object.__setattr__(self, "effect_scope", RecordEffectScope(str(self.effect_scope)))


@dataclass(frozen=True, slots=True)
class CanonicalCrosswalk:
    crosswalk_id: str
    key: CanonicalizationKey
    candidate_id: str
    canonical_id: str
    canonical_version: int

    def __post_init__(self) -> None:
        if not self.crosswalk_id.startswith("crosswalk:nngla:"):
            raise ValueError("crosswalk_id must use crosswalk:nngla: namespace")
        if self.canonical_version < 1:
            raise ValueError("canonical_version must be positive")
        if not self.candidate_id or not self.canonical_id:
            raise ValueError("candidate_id and canonical_id are required")


@dataclass(frozen=True, slots=True)
class CanonicalizationReceipt:
    receipt_id: str
    crosswalk: CanonicalCrosswalk
    staged_record_id: str
    dry_run: bool
    source_payload_sha256: str
    validation_references: tuple[str, ...]
    canonicalized_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.receipt_id.startswith("canonicalization:nngla:"):
            raise ValueError("receipt_id must use canonicalization:nngla: namespace")
        if len(self.source_payload_sha256) != 64:
            raise ValueError("source_payload_sha256 must be a SHA-256 hex digest")
        if self.canonicalized_at.tzinfo is None or self.canonicalized_at.utcoffset() is None:
            raise ValueError("canonicalized_at must be timezone-aware")


class CanonicalizationService:
    """In-memory control plane for idempotency/crosswalk semantics.

    It deliberately does not write PostGIS.  Bundle 14B defines the target SQL
    schema separately; a later adapter/migration executes canonical writes.
    """
    def __init__(self) -> None:
        self._by_key: dict[CanonicalizationKey, CanonicalizationReceipt] = {}
        self._canonical_ids: dict[tuple[str, OperationRuntimeMode], CanonicalizationKey] = {}

    @staticmethod
    def _payload_digest(payload: Mapping[str, object]) -> str:
        encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return sha256(encoded).hexdigest()

    def canonicalize(self, staged: StagedRecord, *, canonical_id: str, canonical_version: int = 1, validation_references=(), dry_run: bool = False) -> CanonicalizationReceipt:
        if staged.state not in {IngestState.VALIDATED, IngestState.CANONICALIZATION_READY}:
            raise ValueError("record must be validated/canonicalization-ready")
        key = CanonicalizationKey(staged.source.dataset_id, staged.source.dataset_version, staged.source.source_record_id, staged.batch.runtime_mode, staged.batch.effect_scope)
        existing = self._by_key.get(key)
        if existing is not None:
            if existing.crosswalk.canonical_id != canonical_id or existing.crosswalk.canonical_version != canonical_version:
                raise ValueError("source record already canonicalized to a different canonical target")
            return existing
        canonical_key = (canonical_id, staged.batch.runtime_mode)
        if canonical_key in self._canonical_ids and self._canonical_ids[canonical_key] != key:
            raise ValueError("canonical identifier already mapped from another source record in this runtime")
        crosswalk = CanonicalCrosswalk(f"crosswalk:nngla:{uuid4()}", key, staged.candidate_id, canonical_id, canonical_version)
        receipt = CanonicalizationReceipt(
            f"canonicalization:nngla:{uuid4()}", crosswalk, staged.staged_record_id, bool(dry_run),
            self._payload_digest(staged.raw_payload), tuple(validation_references),
        )
        if not dry_run:
            self._by_key[key] = receipt
            self._canonical_ids[canonical_key] = key
        return receipt

    def receipts(self) -> tuple[CanonicalizationReceipt, ...]:
        return tuple(self._by_key[k] for k in sorted(self._by_key, key=lambda x: (x.dataset_id, x.dataset_version, x.source_record_id, x.runtime_mode.value, x.effect_scope.value)))


__all__ = ["CanonicalizationKey", "CanonicalCrosswalk", "CanonicalizationReceipt", "CanonicalizationService"]
