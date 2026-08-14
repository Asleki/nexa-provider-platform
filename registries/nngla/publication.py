"""P006.7.2.9 NNGLA publication eligibility and immutable publication records."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from types import MappingProxyType
from collections.abc import Mapping
from uuid import uuid4

from registries.country.operating_context import RecordEffectScope
from shared.runtime.operation_runtime import OperationRuntimeMode
from .canonicalization import CanonicalizationReceipt
from .source_dataset import DataClassification


_PUBLIC_CLASSIFICATIONS = frozenset({DataClassification.PUBLIC, DataClassification.PUBLIC_REFERENCE})


@dataclass(frozen=True, slots=True)
class PublicationEligibility:
    eligible: bool
    reasons: tuple[str, ...]


def evaluate_publication_eligibility(
    receipt: CanonicalizationReceipt,
    *,
    classification: DataClassification | str,
    record_family: str,
) -> PublicationEligibility:
    cls = classification if isinstance(classification, DataClassification) else DataClassification(str(classification))
    reasons: list[str] = []
    if receipt.dry_run:
        reasons.append("DRY_RUN_NOT_PUBLISHABLE")
    if cls not in _PUBLIC_CLASSIFICATIONS:
        reasons.append("CLASSIFICATION_NOT_PUBLIC")
    if not record_family or not record_family.strip():
        reasons.append("RECORD_FAMILY_REQUIRED")
    if not receipt.crosswalk.canonical_id:
        reasons.append("CANONICAL_ID_REQUIRED")
    return PublicationEligibility(not reasons, tuple(reasons))


def _canonical_digest(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")
    return sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class NNGLAPublicationRecord:
    publication_id: str
    publication_version: int
    canonical_id: str
    canonical_version: int
    record_family: str
    canonicalization_receipt_id: str
    runtime_mode: OperationRuntimeMode
    effect_scope: RecordEffectScope
    classification: DataClassification
    visibility: str
    payload: Mapping[str, object] = field(default_factory=dict)
    published_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        if not self.publication_id.startswith("publication:nngla:"):
            raise ValueError("publication_id must use publication:nngla: namespace")
        if self.publication_version < 1 or self.canonical_version < 1:
            raise ValueError("publication and canonical versions must be positive")
        if not self.canonical_id or not self.record_family:
            raise ValueError("canonical_id and record_family are required")
        if not self.canonicalization_receipt_id.startswith("canonicalization:nngla:"):
            raise ValueError("publication must reference an NNGLA canonicalization receipt")
        runtime = OperationRuntimeMode.parse(self.runtime_mode)
        scope = self.effect_scope if isinstance(self.effect_scope, RecordEffectScope) else RecordEffectScope(str(self.effect_scope))
        cls = self.classification if isinstance(self.classification, DataClassification) else DataClassification(str(self.classification))
        if cls not in _PUBLIC_CLASSIFICATIONS:
            raise ValueError("only PUBLIC or PUBLIC_REFERENCE records are publicly publishable")
        if self.visibility != "public":
            raise ValueError("Bundle 14C public publication visibility must be public")
        if self.published_at.tzinfo is None or self.published_at.utcoffset() is None:
            raise ValueError("published_at must be timezone-aware")
        object.__setattr__(self, "runtime_mode", runtime)
        object.__setattr__(self, "effect_scope", scope)
        object.__setattr__(self, "classification", cls)
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
        object.__setattr__(self, "published_at", self.published_at.astimezone(timezone.utc))

    @property
    def content_sha256(self) -> str:
        return _canonical_digest({
            "publication_id": self.publication_id,
            "publication_version": self.publication_version,
            "canonical_id": self.canonical_id,
            "canonical_version": self.canonical_version,
            "record_family": self.record_family,
            "canonicalization_receipt_id": self.canonicalization_receipt_id,
            "runtime_mode": self.runtime_mode.value,
            "effect_scope": self.effect_scope.value,
            "classification": self.classification.value,
            "visibility": self.visibility,
            "payload": dict(self.payload),
        })


class MemoryNNGLAPublicationRepository:
    def __init__(self) -> None:
        self._records: dict[tuple[str, int], NNGLAPublicationRecord] = {}

    def add(self, record: NNGLAPublicationRecord) -> None:
        key = (record.publication_id, record.publication_version)
        if key in self._records:
            raise ValueError("publication version already exists")
        self._records[key] = record

    def get(self, publication_id: str, publication_version: int) -> NNGLAPublicationRecord | None:
        return self._records.get((publication_id, publication_version))

    def list_all(self) -> tuple[NNGLAPublicationRecord, ...]:
        return tuple(self._records[key] for key in sorted(self._records))


class NNGLAPublicationService:
    def __init__(self, repository: MemoryNNGLAPublicationRepository | None = None) -> None:
        self.repository = repository or MemoryNNGLAPublicationRepository()

    def publish(
        self,
        receipt: CanonicalizationReceipt,
        *,
        record_family: str,
        classification: DataClassification | str,
        publication_version: int = 1,
        payload: Mapping[str, object] | None = None,
    ) -> NNGLAPublicationRecord:
        decision = evaluate_publication_eligibility(receipt, classification=classification, record_family=record_family)
        if not decision.eligible:
            raise ValueError("publication ineligible: " + ",".join(decision.reasons))
        cls = classification if isinstance(classification, DataClassification) else DataClassification(str(classification))
        crosswalk = receipt.crosswalk
        record = NNGLAPublicationRecord(
            publication_id=f"publication:nngla:{uuid4()}",
            publication_version=publication_version,
            canonical_id=crosswalk.canonical_id,
            canonical_version=crosswalk.canonical_version,
            record_family=record_family,
            canonicalization_receipt_id=receipt.receipt_id,
            runtime_mode=crosswalk.key.runtime_mode,
            effect_scope=crosswalk.key.effect_scope,
            classification=cls,
            visibility="public",
            payload=dict(payload or {}),
        )
        self.repository.add(record)
        return record


__all__ = [
    "PublicationEligibility", "evaluate_publication_eligibility", "NNGLAPublicationRecord",
    "MemoryNNGLAPublicationRepository", "NNGLAPublicationService",
]
