import pytest
from database.migration_control.locking import MigrationLock
from database.migration_control.errors import MigrationLockError
class A:
 def __init__(self,ok=True): self.ok=ok; self.released=False
 def try_advisory_lock(self,k): return self.ok
 def release_advisory_lock(self,k): self.released=True
def test_lock_release_and_contention():
 a=A();
 with MigrationLock(a).acquire(): pass
 assert a.released
 with pytest.raises(MigrationLockError):
  with MigrationLock(A(False)).acquire(): pass
