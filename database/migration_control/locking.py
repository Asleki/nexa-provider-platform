"""Stable session-owned PostgreSQL advisory-lock boundary."""
from __future__ import annotations
from contextlib import contextmanager
from .constants import ADVISORY_LOCK_KEY
from .errors import MigrationLockError
class MigrationLock:
    def __init__(self,adapter,key:int=ADVISORY_LOCK_KEY): self.adapter=adapter; self.key=key
    @contextmanager
    def acquire(self):
        if not self.adapter.try_advisory_lock(self.key): raise MigrationLockError("another migration controller currently owns the migration lock.")
        try: yield
        finally: self.adapter.release_advisory_lock(self.key)
