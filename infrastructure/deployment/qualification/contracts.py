"""Contracts for deterministic deployment-package qualification."""
from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass(frozen=True, slots=True)
class DeploymentFinding:
    code: str
    passed: bool
    message: str

    def to_dict(self) -> dict:
        return asdict(self)

@dataclass(frozen=True, slots=True)
class DeploymentQualification:
    milestone_id: str
    status: str
    findings: tuple[DeploymentFinding, ...]
    database_writes_performed: int = 0

    def __post_init__(self) -> None:
        expected = "PASSED" if all(item.passed for item in self.findings) else "FAILED"
        if self.status != expected:
            raise ValueError("qualification status disagrees with findings")
        if self.database_writes_performed != 0:
            raise ValueError("deployment qualification must be read-only")

    def to_dict(self) -> dict:
        return {
            "milestoneId": self.milestone_id,
            "status": self.status,
            "findings": [item.to_dict() for item in self.findings],
            "databaseWritesPerformed": self.database_writes_performed,
        }
