"""Immutable deployment and rollback receipts for I006."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Literal

Outcome = Literal["passed", "failed"]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

@dataclass(frozen=True, slots=True)
class DeploymentReceipt:
    deployment_id: str
    release_id: str
    commit_sha: str
    environment_name: str
    outcome: Outcome
    health_url: str
    generated_at: str
    database_writes_performed: int = 0

    def __post_init__(self) -> None:
        if not self.deployment_id.startswith("deploy:"):
            raise ValueError("deployment_id must use deploy: namespace")
        if not self.release_id.startswith("release:"):
            raise ValueError("release_id must use release: namespace")
        if len(self.commit_sha) < 7:
            raise ValueError("commit_sha is too short")
        if self.database_writes_performed != 0:
            raise ValueError("I006 qualification receipts cannot report database writes")

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass(frozen=True, slots=True)
class RollbackReceipt:
    rollback_id: str
    from_release: str
    to_release: str
    outcome: Outcome
    health_status: str
    generated_at: str
    database_writes_performed: int = 0

    def __post_init__(self) -> None:
        if not self.rollback_id.startswith("rollback:"):
            raise ValueError("rollback_id must use rollback: namespace")
        if self.from_release == self.to_release:
            raise ValueError("rollback releases must differ")
        if self.database_writes_performed != 0:
            raise ValueError("application rollback must not imply database writes")

    def to_dict(self) -> dict:
        return asdict(self)
