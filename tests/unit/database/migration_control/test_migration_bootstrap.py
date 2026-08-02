from database.migration_control.bootstrap import MigrationBootstrapService
class A:
 def __init__(self): self.exists=False; self.calls=0
 def ledger_exists(self): return self.exists
 def execute_bootstrap(self,sql): self.calls+=1; self.exists=True
 def verify_bootstrap(self): return self.exists
def test_bootstrap_is_idempotent(tmp_path):
 (tmp_path/'migration_ledger_bootstrap.sql').write_text('CREATE SCHEMA platform;'); a=A(); s=MigrationBootstrapService(a,tmp_path); s.bootstrap(); s.bootstrap(); assert a.calls==1
