import pytest
from registries.adapters.postgresql import PostgreSQLConnectionProvider, PostgreSQLNameRepository
from registries.names import NameRepository, NameNotFoundError

class Cursor:
    def __init__(self, row=None): self.row=row; self.executed=[]
    def execute(self, sql, params=()): self.executed.append((sql,params))
    def fetchone(self): return self.row
class Connection:
    def __init__(self,row=None): self.cur=Cursor(row); self.committed=False; self.rolled_back=False; self.closed=False
    def cursor(self): return self.cur
    def commit(self): self.committed=True
    def rollback(self): self.rolled_back=True
    def close(self): self.closed=True

def test_implements_locked_repository_contract():
    repo=PostgreSQLNameRepository(PostgreSQLConnectionProvider(lambda:Connection()))
    assert isinstance(repo,NameRepository)

def test_get_not_found_preserves_domain_error_and_rolls_back():
    connection=Connection()
    repo=PostgreSQLNameRepository(PostgreSQLConnectionProvider(lambda:connection))
    with pytest.raises(NameNotFoundError): repo.get("missing")
    assert connection.rolled_back and connection.closed
