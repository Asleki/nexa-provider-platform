"""P006.7.2.9 NNGLA domain events and shared-audit linkage.

Bundle 14C is additive: it wraps completed Bundle 14B operation receipts instead
of modifying locked ingest/canonicalization services.  Historical Phase D audit
CSV evidence remains source evidence and is not treated as live runtime audit.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from registries.country.operating_context import RecordEffectScope
from shared.audit.audit_action import AuditAction
from shared.audit.audit_outcome import AuditOutcome
from shared.audit.audit_record import AuditRecord
from shared.events.base_event import BaseEvent
from shared.events.event_metadata import EventMetadata
from shared.runtime.operation_runtime import OperationRuntimeMode


class NNGLAEventType(str, Enum):
    RECORD_CANONICALIZED = "NNGLA_RECORD_CANONICALIZED"
    RECORD_QUARANTINED = "NNGLA_RECORD_QUARANTINED"
    RECORD_PUBLISHED = "NNGLA_RECORD_PUBLISHED"
    FOUNDATION_QUALIFIED = "NNGLA_FOUNDATION_QUALIFIED"


class NNGLAEvent(BaseEvent):
    def __init__(
        self,
        *,
        event_id: str,
        event_type: NNGLAEventType | str,
        occurred_at: datetime,
        subject_id: str,
        record_family: str,
        runtime_mode: OperationRuntimeMode | str,
        effect_scope: RecordEffectScope | str,
        metadata: EventMetadata,
        canonical_version: int | None = None,
        payload: dict[str, object] | None = None,
    ) -> None:
        if not isinstance(subject_id, str) or not subject_id.strip():
            raise ValueError("subject_id is required")
        if not isinstance(record_family, str) or not record_family.strip():
            raise ValueError("record_family is required")
        runtime = OperationRuntimeMode.parse(runtime_mode)
        scope = effect_scope if isinstance(effect_scope, RecordEffectScope) else RecordEffectScope(str(effect_scope))
        if scope is RecordEffectScope.SIMULATION_ONLY and runtime is not OperationRuntimeMode.SIMULATION:
            raise ValueError("SIMULATION_ONLY effect requires simulation runtime")
        if scope is RecordEffectScope.PRODUCTION_ONLY and runtime is not OperationRuntimeMode.PRODUCTION:
            raise ValueError("PRODUCTION_ONLY effect requires production runtime")
        if canonical_version is not None and (isinstance(canonical_version, bool) or not isinstance(canonical_version, int) or canonical_version < 1):
            raise ValueError("canonical_version must be positive when supplied")
        if not isinstance(metadata, EventMetadata):
            raise TypeError("metadata must be EventMetadata")
        et = event_type if isinstance(event_type, NNGLAEventType) else NNGLAEventType(str(event_type))
        body: dict[str, object] = {
            "authority_id": "authority:nngla",
            "country_id": "country:novegeo",
            "realm_id": "realm:nexilabs:novegeo",
            "subject_id": subject_id.strip(),
            "record_family": record_family.strip(),
            "runtime_mode": runtime.value,
            "effect_scope": scope.value,
        }
        if canonical_version is not None:
            body["canonical_version"] = canonical_version
        body.update(dict(payload or {}))
        super().__init__(
            event_id=event_id,
            event_type=et.value,
            event_version=1,
            occurred_at=occurred_at,
            metadata=metadata.to_dict(),
            payload=body,
        )
        self.subject_id = subject_id.strip()
        self.record_family = record_family.strip()
        self.runtime_mode = runtime
        self.effect_scope = scope
        self.canonical_version = canonical_version


@dataclass(frozen=True, slots=True)
class NNGLAMutationTrace:
    event: NNGLAEvent
    audit: AuditRecord


class NNGLAEventFactory:
    @staticmethod
    def create(
        *,
        event_type: NNGLAEventType | str,
        subject_id: str,
        record_family: str,
        runtime_mode: OperationRuntimeMode | str,
        effect_scope: RecordEffectScope | str,
        correlation_id: str,
        actor_id: str,
        canonical_version: int | None = None,
        causation_id: str | None = None,
        device_id: str | None = None,
        occurred_at: datetime | None = None,
        payload: dict[str, object] | None = None,
    ) -> NNGLAMutationTrace:
        when = occurred_at or datetime.now(timezone.utc)
        runtime = OperationRuntimeMode.parse(runtime_mode)
        scope = effect_scope if isinstance(effect_scope, RecordEffectScope) else RecordEffectScope(str(effect_scope))
        et = event_type if isinstance(event_type, NNGLAEventType) else NNGLAEventType(str(event_type))
        metadata = EventMetadata(
            correlation_id=correlation_id,
            causation_id=causation_id,
            actor_id=actor_id,
            device_id=device_id,
            source="nngla",
            attributes={"authority_id": "authority:nngla", "effect_scope": scope.value},
        )
        event = NNGLAEvent(
            event_id=f"nngla-event:{uuid4()}",
            event_type=et,
            occurred_at=when,
            subject_id=subject_id,
            record_family=record_family,
            runtime_mode=runtime,
            effect_scope=scope,
            metadata=metadata,
            canonical_version=canonical_version,
            payload=payload,
        )
        action = {
            NNGLAEventType.RECORD_CANONICALIZED: AuditAction.PROCESS,
            NNGLAEventType.RECORD_QUARANTINED: AuditAction.VALIDATE,
            NNGLAEventType.RECORD_PUBLISHED: AuditAction.PROCESS,
            NNGLAEventType.FOUNDATION_QUALIFIED: AuditAction.VALIDATE,
        }[et]
        audit = AuditRecord(
            audit_id=f"audit:{uuid4()}",
            version=1,
            recorded_at=when,
            action=action,
            outcome=AuditOutcome.SUCCESS,
            actor_id=actor_id,
            actor_type="nngla_actor",
            target_namespace="nngla",
            target_type=record_family.lower(),
            target_id=subject_id,
            runtime_id="realm:nexilabs:novegeo",
            runtime_mode=runtime.value,
            source="nngla",
            event_id=event.event_id,
            event_type=event.event_type,
            correlation_id=correlation_id,
            causation_id=causation_id,
            device_id=device_id,
            metadata={
                "authority_id": "authority:nngla",
                "effect_scope": scope.value,
                "canonical_version": canonical_version,
            },
        )
        return NNGLAMutationTrace(event=event, audit=audit)


__all__ = ["NNGLAEventType", "NNGLAEvent", "NNGLAMutationTrace", "NNGLAEventFactory"]
