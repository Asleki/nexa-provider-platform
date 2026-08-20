"""Additive contracts for P006.7.11.7 Bundle 17.0MR — NNGLA Migration Ready.

The package deliberately consumes the locked Bundle 17E / Bundle 16 migration
contracts instead of changing them. PostgreSQL is the authoritative resume
checkpoint; local files are never treated as proof of committed migration state.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
import json


class DomainDisposition(str, Enum):
    RECONCILE_IMMUTABLE = "RECONCILE_IMMUTABLE"
    BATCH_INSERT_OR_REUSE = "BATCH_INSERT_OR_REUSE"
    CANDIDATE_ONLY = "CANDIDATE_ONLY"
    EMPTY_READY = "EMPTY_READY"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    PENDING_PRODUCTION_RECOGNITION = "PENDING_PRODUCTION_RECOGNITION"
    DEFERRED = "DEFERRED"


class ReconciliationAction(str, Enum):
    INSERT_NEW = "INSERT_NEW"
    REUSE_CANONICAL = "REUSE_CANONICAL"
    CONFLICT = "CONFLICT"


@dataclass(frozen=True, slots=True)
class DomainPlanEntry:
    domain_key: str
    source_path: str
    disposition: DomainDisposition
    expected_count: int
    canonical_target: str
    identity_policy: str
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.domain_key.strip():
            raise ValueError("domain_key is required")
        if not self.source_path.strip():
            raise ValueError("source_path is required")
        if self.expected_count < 0:
            raise ValueError("expected_count cannot be negative")
        if not self.canonical_target.strip():
            raise ValueError("canonical_target is required")
        if not self.identity_policy.strip():
            raise ValueError("identity_policy is required")


@dataclass(frozen=True, slots=True)
class BatchProfile:
    profile_id: str
    expected_total: int
    batch_sizes: tuple[int, ...]
    purpose: str

    def __post_init__(self) -> None:
        if not self.profile_id.strip():
            raise ValueError("profile_id is required")
        if self.expected_total < 1:
            raise ValueError("expected_total must be positive")
        if not self.batch_sizes or any(size < 1 for size in self.batch_sizes):
            raise ValueError("batch_sizes must contain positive integers")
        if sum(self.batch_sizes) != self.expected_total:
            raise ValueError("batch profile sizes must exactly equal expected_total")
        if not self.purpose.strip():
            raise ValueError("purpose is required")


@dataclass(frozen=True, slots=True)
class BatchWindow:
    batch_number: int
    start_offset: int
    end_offset: int
    candidate_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.batch_number < 1:
            raise ValueError("batch_number must be positive")
        if self.start_offset < 0 or self.end_offset < self.start_offset:
            raise ValueError("invalid batch offsets")
        if self.end_offset - self.start_offset != len(self.candidate_ids):
            raise ValueError("batch offsets do not match candidate count")
        if len(self.candidate_ids) != len(set(self.candidate_ids)):
            raise ValueError("candidate IDs inside a batch must be unique")

    @property
    def selected_count(self) -> int:
        return len(self.candidate_ids)


@dataclass(frozen=True, slots=True)
class ReconciliationItem:
    coordinate_candidate_id: str
    canonical_spatial_point_id: str
    geometry_id: str
    action: ReconciliationAction
    reason: str


@dataclass(frozen=True, slots=True)
class EmptyRegisterStatus:
    domain_key: str
    historical_path: str
    operational_path: str
    target_relation: str
    historical_exists: bool
    operational_exists: bool
    historical_row_count: int
    operational_row_count: int
    operational_contract_valid: bool
    target_relation_exists: bool | None = None
    ready: bool = False
    findings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BaselineVerificationReport:
    expected_count: int
    matched_count: int
    missing: tuple[str, ...]
    conflicts: tuple[str, ...]
    sovereign_boundary_ok: bool
    findings: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return (
            self.expected_count == self.matched_count
            and not self.missing
            and not self.conflicts
            and self.sovereign_boundary_ok
            and not self.findings
        )


@dataclass(frozen=True, slots=True)
class CandidateStateReport:
    road_candidate_count: int
    locked_road_count: int
    candidate_only_road_count: int
    feature_candidate_count: int
    feature_reuse_count: int
    feature_pending_recognition_count: int
    feature_deferred_count: int
    findings: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        return (
            self.road_candidate_count == 900
            and self.locked_road_count == 350
            and self.candidate_only_road_count == 550
            and self.feature_candidate_count == 37
            and self.feature_reuse_count == 21
            and self.feature_pending_recognition_count == 5
            and self.feature_deferred_count == 11
            and not self.findings
        )


@dataclass(frozen=True, slots=True)
class TargetPreflight:
    database_name: str
    environment_name: str
    current_user: str
    ssl_enabled: bool
    migration_ledger_applied: int
    migration_ledger_non_applied: int
    required_migrations_missing: tuple[str, ...] = ()
    required_migrations_non_applied: tuple[str, ...] = ()
    required_relations: Mapping[str, bool] = field(default_factory=dict)
    required_functions: Mapping[str, bool] = field(default_factory=dict)
    bundle17e_qualified: bool = False
    empty_registers_ready: bool = False
    candidate_state_ready: bool = False
    immutable_baseline_ready: bool = False
    findings: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return (
            bool(self.database_name)
            and self.ssl_enabled
            and self.migration_ledger_applied >= 18
            and self.migration_ledger_non_applied == 0
            and not self.required_migrations_missing
            and not self.required_migrations_non_applied
            and all(self.required_relations.values())
            and all(self.required_functions.values())
            and self.bundle17e_qualified
            and self.empty_registers_ready
            and self.candidate_state_ready
            and self.immutable_baseline_ready
            and not self.findings
        )


@dataclass(frozen=True, slots=True)
class MigrationPreview:
    database_name: str
    environment_name: str
    profile_id: str
    source_sha256: str
    repository_revision: str
    total_count: int
    insert_count: int
    reuse_count: int
    conflict_count: int
    batches: tuple[BatchWindow, ...]
    reconciliation: tuple[ReconciliationItem, ...]
    fingerprint: str

    @property
    def execution_ready(self) -> bool:
        return self.total_count == 2411 and self.conflict_count == 0

    @classmethod
    def build(
        cls,
        *,
        database_name: str,
        environment_name: str,
        profile_id: str,
        source_sha256: str,
        repository_revision: str,
        batches: Sequence[BatchWindow],
        reconciliation: Sequence[ReconciliationItem],
    ) -> "MigrationPreview":
        items = tuple(reconciliation)
        windows = tuple(batches)
        counts = {
            action: sum(1 for item in items if item.action is action)
            for action in ReconciliationAction
        }
        payload = {
            "database_name": database_name,
            "environment_name": environment_name,
            "profile_id": profile_id,
            "source_sha256": source_sha256,
            "repository_revision": repository_revision,
            "batches": [list(batch.candidate_ids) for batch in windows],
            "reconciliation": [
                {
                    "candidate": item.coordinate_candidate_id,
                    "canonical": item.canonical_spatial_point_id,
                    "geometry": item.geometry_id,
                    "action": item.action.value,
                    "reason": item.reason,
                }
                for item in items
            ],
        }
        fingerprint = sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return cls(
            database_name=database_name,
            environment_name=environment_name,
            profile_id=profile_id,
            source_sha256=source_sha256,
            repository_revision=repository_revision,
            total_count=len(items),
            insert_count=counts[ReconciliationAction.INSERT_NEW],
            reuse_count=counts[ReconciliationAction.REUSE_CANONICAL],
            conflict_count=counts[ReconciliationAction.CONFLICT],
            batches=windows,
            reconciliation=items,
            fingerprint=fingerprint,
        )


@dataclass(frozen=True, slots=True)
class BatchExecutionResult:
    batch_number: int
    selected_count: int
    inserted_count: int
    reused_count: int
    status: str
    execution_id: str
    candidate_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.status not in {"APPLIED", "REUSED"}:
            raise ValueError("batch execution status must be APPLIED or REUSED")
        if self.selected_count != self.inserted_count + self.reused_count:
            raise ValueError("batch execution counts do not reconcile")


@dataclass(frozen=True, slots=True)
class VerificationReport:
    database_name: str
    expected_spatial_count: int
    canonical_count: int
    geometry_count: int
    crosswalk_count: int
    receipt_item_count: int
    missing_candidate_ids: tuple[str, ...]
    conflicting_candidate_ids: tuple[str, ...]
    empty_registers_ready: bool
    immutable_baseline_findings: tuple[str, ...]
    candidate_state_findings: tuple[str, ...]
    findings: tuple[str, ...]

    @property
    def passed(self) -> bool:
        return (
            self.expected_spatial_count == self.canonical_count
            == self.geometry_count
            == self.crosswalk_count
            == self.receipt_item_count
            and not self.missing_candidate_ids
            and not self.conflicting_candidate_ids
            and self.empty_registers_ready
            and not self.immutable_baseline_findings
            and not self.candidate_state_findings
            and not self.findings
        )


__all__ = [
    "DomainDisposition",
    "ReconciliationAction",
    "DomainPlanEntry",
    "BatchProfile",
    "BatchWindow",
    "ReconciliationItem",
    "EmptyRegisterStatus",
    "BaselineVerificationReport",
    "CandidateStateReport",
    "TargetPreflight",
    "MigrationPreview",
    "BatchExecutionResult",
    "VerificationReport",
]
