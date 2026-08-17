"""Framework-neutral runtime command dispatcher."""
from __future__ import annotations
from datetime import datetime, timezone
from uuid import uuid4
from collections.abc import Callable, Mapping
from .authorization import authorize
from .command_catalogue import get_command_definition
from .contracts import CommandReceipt, CommandStatus, RuntimeCommand, RuntimePrincipal
from .idempotency import MemoryCommandReceiptStore, command_fingerprint
from .validation import validate_command

class CommandRejected(ValueError):
    def __init__(self, reasons):
        self.reasons = tuple(reasons)
        super().__init__("command rejected: " + ",".join(self.reasons))

CommandHandler = Callable[[RuntimeCommand], Mapping[str, object]]

class RuntimeCommandDispatcher:
    def __init__(self, *, receipt_store=None):
        self.receipt_store = receipt_store or MemoryCommandReceiptStore()
        self._handlers: dict[str, CommandHandler] = {}
    def register_handler(self, handler_key: str, handler: CommandHandler) -> None:
        if not handler_key.strip() or not callable(handler): raise ValueError("handler key and callable are required")
        self._handlers[handler_key] = handler
    def execute(self, command: RuntimeCommand, principal: RuntimePrincipal, *, approval_granted: bool = False) -> CommandReceipt:
        definition = get_command_definition(command.command_code, command.command_version)
        decision = authorize(command, principal, approval_granted=approval_granted)
        if not decision.allowed: raise CommandRejected(decision.reasons)
        findings = validate_command(command)
        if findings: raise CommandRejected(tuple(item.error_code for item in findings))
        fingerprint = command_fingerprint(command)
        replay = self.receipt_store.replay(command, fingerprint)
        if replay is not None: return replay
        handler = self._handlers.get(definition.handler_key)
        if handler is None: raise CommandRejected(("DOMAIN_HANDLER_NOT_REGISTERED",))
        result = dict(handler(command))
        references = tuple(sorted((str(k), str(v)) for k,v in dict(result.get("references", {})).items()))
        receipt = CommandReceipt(
            receipt_id=f"runtime-command:nngla:{uuid4()}",
            command_code=command.command_code,
            command_version=command.command_version,
            runtime_mode=command.runtime_mode.value,
            effect_scope=command.effect_scope,
            principal_id=command.principal_id,
            idempotency_key=command.idempotency_key,
            request_fingerprint=fingerprint,
            status=CommandStatus.COMPLETED,
            references=references,
            event_id=str(result["event_id"]) if result.get("event_id") else None,
            audit_id=str(result["audit_id"]) if result.get("audit_id") else None,
            replayed=False,
            completed_at=datetime.now(timezone.utc),
        )
        self.receipt_store.store(command, fingerprint, receipt)
        return receipt

__all__ = ["CommandRejected","CommandHandler","RuntimeCommandDispatcher"]
