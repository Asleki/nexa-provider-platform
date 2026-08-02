from datetime import datetime, timezone
from database.migration_control.recovery import *
from database.migration_control.ledger import MemoryMigrationLedger, MigrationLedgerRecord

class Drift:
    def __init__(self, clean): self.clean=clean
    def inspect_expected(self, plan): return type('R',(),{'is_clean':self.clean})()

def rec(status='STARTED'):
    return MigrationLedgerRecord('m1','M1','m1.sql',1,'a'*64,status,'e1',datetime.now(timezone.utc))

def definition():
    return type('D',(),{'identity':type('I',(),{'migration_id':'m1'})()})()

def test_started_with_objects_requires_reconciliation():
    ledger=MemoryMigrationLedger(); ledger.insert_started(rec())
    d=MigrationRecoveryService(ledger,Drift(True)).assess(definition(),None)
    assert d.action is RecoveryAction.RECONCILE_APPLIED

def test_started_without_objects_stops():
    ledger=MemoryMigrationLedger(); ledger.insert_started(rec())
    assert MigrationRecoveryService(ledger,Drift(False)).assess(definition(),None).action is RecoveryAction.STOP

def test_reconciliation_only_transitions_started():
    ledger=MemoryMigrationLedger(); ledger.insert_started(rec())
    out=MigrationRecoveryService(ledger,Drift(True)).reconcile_applied('m1',completed_at=datetime.now(timezone.utc))
    assert out.status=='APPLIED'
