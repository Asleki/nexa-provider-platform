"""P006.7.11.5 execution receipt and item contracts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json

@dataclass(frozen=True, slots=True)
class ExecutionItemReceipt:
    source_record_id: str
    outcome: str
    canonical_id: str | None = None
    crosswalk_id: str | None = None
    canonicalization_receipt_id: str | None = None
    event_id: str | None = None
    audit_id: str | None = None
    publication_ready: bool = False
    detail: dict[str, object] | None = None

@dataclass(frozen=True, slots=True)
class ExecutionReceipt:
    execution_id: str
    plan_id: str
    plan_version: int
    fingerprint: str
    database_name: str
    environment_name: str
    runtime_mode: str
    repository_revision: str
    source_sha256: str
    submitter_actor_id: str
    approver_actor_id: str
    selected_count: int
    inserted_count: int
    reused_count: int
    quarantined_count: int
    failed_count: int
    status: str
    started_at: datetime
    completed_at: datetime
    items: tuple[ExecutionItemReceipt, ...]

    @property
    def content_sha256(self) -> str:
        payload = {
            "execution_id": self.execution_id, "plan_id": self.plan_id, "plan_version": self.plan_version,
            "fingerprint": self.fingerprint, "database_name": self.database_name, "environment_name": self.environment_name,
            "runtime_mode": self.runtime_mode, "repository_revision": self.repository_revision,
            "source_sha256": self.source_sha256, "submitter_actor_id": self.submitter_actor_id,
            "approver_actor_id": self.approver_actor_id, "selected_count": self.selected_count,
            "inserted_count": self.inserted_count, "reused_count": self.reused_count,
            "quarantined_count": self.quarantined_count, "failed_count": self.failed_count, "status": self.status,
            "items": [item.__dict__ if hasattr(item, "__dict__") else {
                "source_record_id": item.source_record_id, "outcome": item.outcome, "canonical_id": item.canonical_id,
                "crosswalk_id": item.crosswalk_id, "canonicalization_receipt_id": item.canonicalization_receipt_id,
                "event_id": item.event_id, "audit_id": item.audit_id, "publication_ready": item.publication_ready,
                "detail": item.detail or {},
            } for item in self.items],
        }
        return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def utc_now() -> datetime:
    return datetime.now(timezone.utc)

__all__ = ["ExecutionItemReceipt", "ExecutionReceipt", "utc_now"]
