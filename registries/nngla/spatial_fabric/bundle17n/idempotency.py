"""Semantic idempotency with collision rejection."""
from __future__ import annotations
from dataclasses import replace
from threading import Lock
from ._shared import semantic_fingerprint
from .contracts import CommandReceipt, RuntimeCommand

class CommandIdempotencyConflict(ValueError): pass

def command_fingerprint(command: RuntimeCommand) -> str:
    return semantic_fingerprint({
        "command_code": command.command_code,
        "command_version": command.command_version,
        "runtime_mode": command.runtime_mode.value,
        "effect_scope": command.effect_scope,
        "principal_id": command.principal_id,
        "payload": dict(command.payload),
    })

class MemoryCommandReceiptStore:
    def __init__(self):
        self._lock = Lock()
        self._records: dict[tuple[str,str,str], tuple[str, CommandReceipt]] = {}
    @staticmethod
    def key(command: RuntimeCommand) -> tuple[str,str,str]:
        return (command.runtime_mode.value, command.command_code, command.idempotency_key)
    def replay(self, command: RuntimeCommand, fingerprint: str) -> CommandReceipt | None:
        with self._lock:
            existing = self._records.get(self.key(command))
            if existing is None: return None
            old_fingerprint, receipt = existing
            if old_fingerprint != fingerprint:
                raise CommandIdempotencyConflict("idempotency key was already used with different command semantics")
            return replace(receipt, replayed=True)
    def store(self, command: RuntimeCommand, fingerprint: str, receipt: CommandReceipt) -> None:
        with self._lock:
            key = self.key(command)
            existing = self._records.get(key)
            if existing is not None:
                if existing[0] != fingerprint: raise CommandIdempotencyConflict("idempotency collision")
                return
            self._records[key] = (fingerprint, receipt)

__all__ = ["CommandIdempotencyConflict","command_fingerprint","MemoryCommandReceiptStore"]
