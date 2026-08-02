"""Failure classification and conservative recovery decisions."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from .errors import MigrationRecoveryError

class FailureClass(str, Enum):
    PRE_EXECUTION_FAILURE='PRE_EXECUTION_FAILURE'; LOCK_FAILURE='LOCK_FAILURE'
    TARGET_MISMATCH='TARGET_MISMATCH'; CHECKSUM_MISMATCH='CHECKSUM_MISMATCH'
    EXECUTION_FAILURE='EXECUTION_FAILURE'; LEDGER_FAILURE='LEDGER_FAILURE'
    POST_VERIFY_FAILURE='POST_VERIFY_FAILURE'; DATABASE_DRIFT='DATABASE_DRIFT'
    INTERRUPTED_OPERATION='INTERRUPTED_OPERATION'

class RecoveryAction(str, Enum):
    RETRY='RETRY'; RECONCILE_APPLIED='RECONCILE_APPLIED'; REQUIRE_FORWARD_FIX='REQUIRE_FORWARD_FIX'; STOP='STOP'

@dataclass(frozen=True, slots=True)
class RecoveryDecision:
    migration_id: str; failure_class: FailureClass; action: RecoveryAction; reason: str

class MigrationRecoveryService:
    def __init__(self, ledger, drift_inspector): self.ledger=ledger; self.drift_inspector=drift_inspector
    def assess(self, definition, plan):
        record=self.ledger.get(definition.identity.migration_id)
        if record is None: return RecoveryDecision(definition.identity.migration_id,FailureClass.PRE_EXECUTION_FAILURE,RecoveryAction.RETRY,'No durable execution record exists.')
        if record.status=='APPLIED': return RecoveryDecision(record.migration_id,FailureClass.POST_VERIFY_FAILURE,RecoveryAction.STOP,'Migration is already applied.')
        if record.status=='FAILED': return RecoveryDecision(record.migration_id,FailureClass.EXECUTION_FAILURE,RecoveryAction.RETRY,'Failed execution may be retried only after structural inspection.')
        report=self.drift_inspector.inspect_expected(type('P',(),{'forward_order':(definition,)})())
        if report.is_clean: return RecoveryDecision(record.migration_id,FailureClass.INTERRUPTED_OPERATION,RecoveryAction.RECONCILE_APPLIED,'Expected objects exist; operator reconciliation is required.')
        return RecoveryDecision(record.migration_id,FailureClass.INTERRUPTED_OPERATION,RecoveryAction.STOP,'Outcome is uncertain and expected objects are incomplete.')
    def reconcile_applied(self, migration_id, *, completed_at, duration_ms=0):
        record=self.ledger.get(migration_id)
        if record is None or record.status!='STARTED': raise MigrationRecoveryError('Only a STARTED migration may be reconciled.')
        self.ledger.mark_applied(migration_id,completed_at=completed_at,duration_ms=duration_ms)
        return self.ledger.get(migration_id)
