from database.migration_control.qualification import MigrationQualificationService
class C:
    def status(self): return type('S',(),{'ledger_state':'BOOTSTRAPPED','pending_migrations':0,'applied_migrations':4})()
    def trusted_plan(self): return type('P',(),{'plan_checksum':'a'*64,'forward_order':()})()
class D:
    def inspect_expected(self,p): return type('R',(),{'is_clean':True})()
def test_qualification_has_deterministic_steps_and_receipt():
    target=type('T',(),{'database_name':'npp_dev','ssl_enabled':True})()
    r=MigrationQualificationService(C(),object(),D()).qualify(target,'development')
    assert r.drift_clean and r.steps==MigrationQualificationService.STEPS and r.receipt.status=='QUALIFIED'
