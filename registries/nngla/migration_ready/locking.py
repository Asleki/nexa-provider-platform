"""Session-level PostgreSQL advisory lock for one active NNGLA migration operator."""
from __future__ import annotations

from contextlib import contextmanager
from hashlib import sha256

LOCK_MATERIAL = "P006.7.11.7:Bundle17.0MR:NNGLA-Migration-Ready"
_raw = int.from_bytes(sha256(LOCK_MATERIAL.encode("utf-8")).digest()[:8], "big", signed=False)
LOCK_KEY = _raw - (1 << 64) if _raw >= (1 << 63) else _raw


class MigrationReadyLockError(RuntimeError):
    pass


@contextmanager
def postgresql_migration_lock(connection):
    """Hold one session lock across all batch transactions.

    The lock is automatically released by PostgreSQL if the connection is lost,
    which makes it appropriate for mobile/network-interruption recovery.
    """
    with connection.cursor() as cur:
        cur.execute("SELECT pg_try_advisory_lock(%s::bigint)", (LOCK_KEY,))
        acquired = bool(cur.fetchone()[0])
    if not acquired:
        raise MigrationReadyLockError("another NNGLA Migration Ready execution session already holds the lock")
    try:
        yield
    finally:
        try:
            with connection.cursor() as cur:
                cur.execute("SELECT pg_advisory_unlock(%s::bigint)", (LOCK_KEY,))
                cur.fetchone()
        except Exception:
            # A dropped connection already releases PostgreSQL session locks.
            pass


__all__ = ["LOCK_MATERIAL", "LOCK_KEY", "MigrationReadyLockError", "postgresql_migration_lock"]
