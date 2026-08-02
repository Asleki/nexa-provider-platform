from pathlib import Path
import pytest
from database.migration_control.executor import MigrationExecutor
from database.migration_control.ledger import MemoryMigrationLedger
from database.migration_control.errors import MigrationExecutionError
class Def:
 class I: migration_id='m'; milestone_id='M'; sequence_number=1
 class F: relative_path='m.sql'; sha256='a'*64; transaction_policy='embedded'
 identity=I(); forward=F()
class A:
 def __init__(self,fail=False): self.fail=fail
 def execute_migration(self,sql,policy):
  if self.fail: raise RuntimeError('boom')
def test_executor_success_and_failure(tmp_path):
 (tmp_path/'m.sql').write_text('SELECT 1;'); l=MemoryMigrationLedger(); assert MigrationExecutor(A(),tmp_path).execute(Def(),l,applied_by='u',database_name='d',environment_name='development').status=='APPLIED'
 l2=MemoryMigrationLedger()
 with pytest.raises(MigrationExecutionError): MigrationExecutor(A(True),tmp_path).execute(Def(),l2,applied_by='u',database_name='d',environment_name='development')
 assert l2.get('m').status=='FAILED'
