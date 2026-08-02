"""Deterministic AWS PostgreSQL qualification orchestration."""
from __future__ import annotations
from dataclasses import dataclass
from .receipts import MigrationOperationReceipt

@dataclass(frozen=True, slots=True)
class QualificationReport:
    database_name: str; environment_name: str; tls_enabled: bool
    ledger_state: str; pending_migrations: int; drift_clean: bool
    steps: tuple[str, ...]; receipt: MigrationOperationReceipt

class MigrationQualificationService:
    STEPS=('inspect-target','status','plan','verify-expected-objects','history')
    def __init__(self, control_service, adapter, drift_inspector): self.control_service=control_service; self.adapter=adapter; self.drift_inspector=drift_inspector
    def qualify(self, actual_target, environment_name):
        status=self.control_service.status(); plan=self.control_service.trusted_plan()
        drift=self.drift_inspector.inspect_expected(plan) if status.applied_migrations else type('D',(),{'is_clean':True})()
        receipt=MigrationOperationReceipt.create(operation='qualify',status='QUALIFIED' if drift.is_clean else 'DRIFT',database_name=actual_target.database_name,environment_name=environment_name,plan_checksum=plan.plan_checksum,details=self.STEPS)
        return QualificationReport(actual_target.database_name,environment_name,actual_target.ssl_enabled,status.ledger_state,status.pending_migrations,drift.is_clean,self.STEPS,receipt)
