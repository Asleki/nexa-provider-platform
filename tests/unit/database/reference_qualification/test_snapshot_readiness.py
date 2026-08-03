from types import SimpleNamespace
from database.reference_qualification.catalogue_snapshot import catalogue_fingerprint
from database.reference_qualification.readiness_verifier import verify_readiness
from registries.name_authority.production_context import MemoryNameContextRepository

def test_snapshot_is_deterministic():
    n=[SimpleNamespace(name_id='n',runtime_mode='simulation',name_kind=SimpleNamespace(value='first_name'),search_value='x')]
    assert catalogue_fingerprint(n,[],[])==catalogue_fingerprint(n,[],[])

def test_readiness_reports_missing_context():
    n=[SimpleNamespace(name_id='n')]; r=verify_readiness(n,MemoryNameContextRepository()); assert r['passed'] is False and r['missing']==('n',)
