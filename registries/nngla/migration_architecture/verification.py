"""P006.7.11.6 execution verification and idempotency qualification."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True,slots=True)
class VerificationReport:
    execution_id:str; passed:bool; findings:tuple[str,...]

def verify_receipt(receipt)->VerificationReport:
    findings=[]
    if receipt.selected_count != receipt.inserted_count+receipt.reused_count+receipt.quarantined_count+receipt.failed_count:
        findings.append("COUNT_RECONCILIATION_FAILED")
    if receipt.failed_count: findings.append("EXECUTION_HAS_FAILURES")
    if len(receipt.fingerprint)!=64: findings.append("FINGERPRINT_INVALID")
    if receipt.submitter_actor_id==receipt.approver_actor_id: findings.append("GOVERNANCE_SEPARATION_FAILED")
    return VerificationReport(receipt.execution_id,not findings,tuple(findings))

def qualify_rerun(first,second)->VerificationReport:
    findings=[]
    if first.fingerprint!=second.fingerprint: findings.append("RERUN_FINGERPRINT_CHANGED")
    if second.inserted_count!=0: findings.append("RERUN_CREATED_NEW_CANONICAL_RECORDS")
    if second.selected_count!=second.reused_count+second.quarantined_count+second.failed_count: findings.append("RERUN_NOT_FULLY_ACCOUNTED")
    return VerificationReport(second.execution_id,not findings,tuple(findings))

__all__=["VerificationReport","verify_receipt","qualify_rerun"]
