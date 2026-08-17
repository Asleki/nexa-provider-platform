"""Governed bulk execution policies and transaction boundary."""
from __future__ import annotations
from contextlib import nullcontext
from uuid import uuid4
from ._shared import BULK_POLICY_PATH, bool_text, csv_rows
from .contracts import BulkAtomicity, BulkExecutionResult, RuntimeCommand, RuntimePrincipal
from .dispatcher import RuntimeCommandDispatcher

def bulk_policies() -> tuple[dict[str,str], ...]: return csv_rows(BULK_POLICY_PATH)

def get_bulk_policy(policy_code: str) -> dict[str,str]:
    for row in bulk_policies():
        if row["bulk_policy_code"] == policy_code and row["status"] == "ACTIVE": return row
    raise KeyError(f"unknown bulk policy: {policy_code}")

class RuntimeBulkExecutor:
    def __init__(self, dispatcher: RuntimeCommandDispatcher, *, transaction_factory=None):
        self.dispatcher = dispatcher
        self.transaction_factory = transaction_factory
    def execute(self, commands: tuple[RuntimeCommand,...], principal: RuntimePrincipal, *, policy_code: str, approval_granted: bool=False) -> BulkExecutionResult:
        policy = get_bulk_policy(policy_code)
        if len(commands) > int(policy["maximum_items"]): raise ValueError("bulk item limit exceeded")
        atomicity = BulkAtomicity(policy["atomicity"])
        if atomicity is BulkAtomicity.PREVIEW_ONLY:
            return BulkExecutionResult(f"bulk:nngla:{uuid4()}", policy_code, atomicity, (), 0, True)
        if atomicity is BulkAtomicity.ALL_OR_NOTHING and self.transaction_factory is None:
            raise RuntimeError("ALL_OR_NOTHING bulk execution requires an injected transaction boundary")
        context = self.transaction_factory() if self.transaction_factory is not None else nullcontext()
        receipts=[]; failures=0
        with context:
            for command in commands:
                try:
                    receipts.append(self.dispatcher.execute(command, principal, approval_granted=approval_granted))
                except Exception:
                    failures += 1
                    if atomicity is BulkAtomicity.ALL_OR_NOTHING or not bool_text(policy["continue_after_item_failure"]):
                        raise
        return BulkExecutionResult(f"bulk:nngla:{uuid4()}", policy_code, atomicity, tuple(receipts), failures, False)

__all__ = ["bulk_policies","get_bulk_policy","RuntimeBulkExecutor"]
