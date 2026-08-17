"""Stable runtime command contracts for P006.7.11.7.18."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from collections.abc import Mapping
from shared.runtime.operation_runtime import OperationRuntimeMode

class CommandStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"

class BulkAtomicity(str, Enum):
    ALL_OR_NOTHING = "ALL_OR_NOTHING"
    ITEM_ATOMIC_CONTINUE = "ITEM_ATOMIC_CONTINUE"
    PREVIEW_ONLY = "PREVIEW_ONLY"

@dataclass(frozen=True, slots=True)
class RuntimePrincipal:
    principal_id: str
    runtime_mode: OperationRuntimeMode | str
    permissions: frozenset[str]
    def __post_init__(self):
        if not self.principal_id.strip(): raise ValueError("principal_id is required")
        object.__setattr__(self, "runtime_mode", OperationRuntimeMode.parse(self.runtime_mode))
        object.__setattr__(self, "permissions", frozenset(str(x).strip() for x in self.permissions if str(x).strip()))

@dataclass(frozen=True, slots=True)
class RuntimeCommand:
    command_code: str
    command_version: int
    runtime_mode: OperationRuntimeMode | str
    effect_scope: str
    principal_id: str
    idempotency_key: str
    correlation_id: str
    payload: Mapping[str, object] = field(default_factory=dict)
    causation_id: str | None = None
    requested_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    def __post_init__(self):
        if not self.command_code.strip(): raise ValueError("command_code is required")
        if self.command_version < 1: raise ValueError("command_version must be positive")
        runtime = OperationRuntimeMode.parse(self.runtime_mode)
        if not self.principal_id.strip(): raise ValueError("principal_id is required")
        if not self.idempotency_key.strip(): raise ValueError("idempotency_key is required")
        if not self.correlation_id.strip(): raise ValueError("correlation_id is required")
        if not self.effect_scope.strip(): raise ValueError("effect_scope is required")
        if self.requested_at.tzinfo is None or self.requested_at.utcoffset() is None:
            raise ValueError("requested_at must be timezone-aware")
        object.__setattr__(self, "runtime_mode", runtime)
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))
        object.__setattr__(self, "requested_at", self.requested_at.astimezone(timezone.utc))

@dataclass(frozen=True, slots=True)
class CommandDefinition:
    command_code: str
    command_version: int
    domain_code: str
    target_family: str
    action_code: str
    handler_key: str
    allowed_runtimes: frozenset[str]
    effect_scope_policy: str
    identity_allocation_policy: str
    approval_requirement: str
    bulk_policy_code: str
    status: str

@dataclass(frozen=True, slots=True)
class AuthorizationDecision:
    allowed: bool
    reasons: tuple[str, ...]

@dataclass(frozen=True, slots=True)
class ValidationFinding:
    rule_id: str
    error_code: str
    field_name: str
    message: str

@dataclass(frozen=True, slots=True)
class CommandReceipt:
    receipt_id: str
    command_code: str
    command_version: int
    runtime_mode: str
    effect_scope: str
    principal_id: str
    idempotency_key: str
    request_fingerprint: str
    status: CommandStatus
    references: tuple[tuple[str, str], ...]
    event_id: str | None
    audit_id: str | None
    replayed: bool
    completed_at: datetime

@dataclass(frozen=True, slots=True)
class BulkExecutionResult:
    operation_id: str
    policy_code: str
    atomicity: BulkAtomicity
    receipts: tuple[CommandReceipt, ...]
    failure_count: int
    preview_only: bool

__all__ = [
    "CommandStatus","BulkAtomicity","RuntimePrincipal","RuntimeCommand","CommandDefinition",
    "AuthorizationDecision","ValidationFinding","CommandReceipt","BulkExecutionResult",
]
