import pytest
from pathlib import Path
from database.migration_control.rollback import MigrationRollbackService
from database.migration_control.errors import MigrationRollbackError

class A:
    def __init__(self): self.calls=[]
    def execute_migration(self,sql,policy): self.calls.append((sql,policy))

def test_production_rollback_is_refused(tmp_path):
    d=type('D',(),{'rollback':type('R',(),{'relative_path':'r.sql','transaction_policy':'embedded'})()})()
    (tmp_path/'r.sql').write_text('ROLLBACK SQL')
    with pytest.raises(MigrationRollbackError): MigrationRollbackService(A(),tmp_path).execute(d,environment_name='production',confirmed=True)

def test_development_rollback_requires_confirmation_and_executes(tmp_path):
    d=type('D',(),{'rollback':type('R',(),{'relative_path':'r.sql','transaction_policy':'embedded'})()})()
    (tmp_path/'r.sql').write_text('ROLLBACK SQL'); a=A(); s=MigrationRollbackService(a,tmp_path)
    with pytest.raises(MigrationRollbackError): s.execute(d,environment_name='development',confirmed=False)
    s.execute(d,environment_name='development',confirmed=True)
    assert a.calls==[('ROLLBACK SQL','embedded')]
