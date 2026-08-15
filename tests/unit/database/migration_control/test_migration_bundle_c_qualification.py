from database.migration_control.qualification import MigrationQualificationService
class C:
    def status(self): return type('S',(),{'ledger_state':'BOOTSTRAPPED','pending_migrations':0,'applied_migrations':4})()
    def trusted_plan(self): return type('P',(),{'plan_checksum':'a'*64,'forward_order':()})()
    def applied_structure_plan(self): return type('P',(),{'forward_order':()})()
class D:
    def inspect_expected(self,p): return type('R',(),{'is_clean':True})()
def test_qualification_has_deterministic_steps_and_receipt():
    target=type('T',(),{'database_name':'npp_dev','ssl_enabled':True})()
    r=MigrationQualificationService(C(),object(),D()).qualify(target,'development')
    assert r.drift_clean and r.steps==MigrationQualificationService.STEPS and r.receipt.status=='QUALIFIED'


class PendingControl:
    def __init__(self):
        self.full = tuple(type('Def', (), {'identity': type('I', (), {'migration_id': f'm{i}'})()})() for i in range(1, 11))
        self.applied = self.full[:6]

    def status(self):
        return type('S', (), {'ledger_state': 'BOOTSTRAPPED', 'pending_migrations': 4, 'applied_migrations': 6})()

    def trusted_plan(self):
        return type('P', (), {'plan_checksum': 'b' * 64, 'forward_order': self.full})()

    def applied_structure_plan(self):
        return type('P', (), {'forward_order': self.applied})()


class RecordingDrift:
    def __init__(self):
        self.ids = ()

    def inspect_expected(self, plan):
        self.ids = tuple(item.identity.migration_id for item in plan.forward_order)
        return type('R', (), {'is_clean': True})()


def test_qualification_treats_missing_pending_structure_as_normal_and_checks_applied_scope_only():
    control = PendingControl()
    drift = RecordingDrift()
    target = type('T', (), {'database_name': 'npp_dev', 'ssl_enabled': True})()

    report = MigrationQualificationService(control, object(), drift).qualify(target, 'development')

    assert drift.ids == tuple(f'm{i}' for i in range(1, 7))
    assert report.pending_migrations == 4
    assert report.drift_clean is True
    assert report.receipt.status == 'QUALIFIED'
