"""Immutable recovery and qualification receipts."""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

@dataclass(frozen=True, slots=True)
class MigrationOperationReceipt:
    receipt_id: str
    operation: str
    status: str
    database_name: str
    environment_name: str
    plan_checksum: str
    details: tuple[str, ...]
    created_at: datetime

    @classmethod
    def create(cls, *, operation: str, status: str, database_name: str,
               environment_name: str, plan_checksum: str = "", details=()):
        return cls(str(uuid4()), operation, status, database_name, environment_name,
                   plan_checksum, tuple(details), datetime.now(timezone.utc))
