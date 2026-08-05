from contextlib import contextmanager
from infrastructure.database.runtime import DatabaseRuntimeSettings,PostgreSQLPool
class Cursor:
    def __enter__(self): return self
    def __exit__(self,*a): pass
    def execute(self,sql): self.sql=sql
    def fetchone(self): return (1,)
class Conn:
    def cursor(self): return Cursor()
class Pool:
    @contextmanager
    def connection(self): yield Conn()
    def close(self): self.closed=True
def test_pool_lifecycle_and_readiness():
    p=PostgreSQLPool(DatabaseRuntimeSettings("db",5432,"npp","u","p"),lambda s:Pool())
    p.open(); assert p.is_open and p.readiness(); p.close(); assert not p.is_open
