import pytest

from registries.nngla.migration_ready.locking import (
    LOCK_KEY, MigrationReadyLockError, postgresql_migration_lock,
)


class Cursor:
    def __init__(self, connection):
        self.connection = connection
        self.row = None
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, params=None):
        assert params == (LOCK_KEY,)
        if "pg_try_advisory_lock" in sql:
            self.row = (self.connection.acquire,)
            if self.connection.acquire:
                self.connection.held = True
        elif "pg_advisory_unlock" in sql:
            self.connection.held = False
            self.row = (True,)
        else:
            raise AssertionError(sql)
    def fetchone(self): return self.row


class Connection:
    def __init__(self, acquire=True):
        self.acquire = acquire
        self.held = False
    def cursor(self): return Cursor(self)


def test_session_lock_is_held_across_batch_scope_and_released_afterward():
    connection = Connection()
    with postgresql_migration_lock(connection):
        assert connection.held
    assert not connection.held


def test_second_operator_fails_closed_when_lock_is_busy():
    with pytest.raises(MigrationReadyLockError, match="another NNGLA"):
        with postgresql_migration_lock(Connection(acquire=False)):
            pass
