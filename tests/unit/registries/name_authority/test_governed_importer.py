import json,hashlib,itertools
from datetime import datetime,timezone
from registries.name_authority import ProductionSeedLoader,GovernedAtomicNameImporter
from registries.names.memory_name_repository import MemoryNameRepository

def test_governed_import_validates_and_imports_then_is_idempotent(tmp_path):
    csv='id,first_name,gender\n1,Ada,Female\n2,José,Male\n'; p=tmp_path/'names.csv'; p.write_text(csv,encoding='utf-8')
    data={"manifest_schema":"npp.production-seed-manifest","manifest_schema_version":1,"classification":"production_seed","status":"approved","encoding":"utf-8","delimiter":",","runtime_policy":{"eligible_runtime_modes":["simulation","production"]},"governance":{"direct_sql_import_allowed":False,"postgresql_copy_allowed":False,"python_validation_required":True},"dataset_id":"dataset.test","dataset_version":1,"dataset_name":"Test","domain":"name_catalogue","source_family":"test","files":[{"file_id":"file.names","path":"names.csv","record_role":"atomic_name","required_headers":["id","first_name","gender"],"row_count":2,"sha256":hashlib.sha256(p.read_bytes()).hexdigest(),"import_enabled":True,"target_name_kind":"first_name","column_mappings":{"id":"external_record_id","first_name":"raw_name_value","gender":"sex_usage"}}]}
    (tmp_path/'manifest.json').write_text(json.dumps(data),encoding='utf-8')
    loader=ProductionSeedLoader(tmp_path); m=loader.load_manifest(tmp_path/'manifest.json'); repo=MemoryNameRepository(); ids=(f'name:{i}' for i in itertools.count(1)); clock=lambda:datetime(2026,8,1,tzinfo=timezone.utc)
    svc=GovernedAtomicNameImporter(loader,repo,clock=clock,name_id_factory=lambda:next(ids))
    first=svc.run(m,runtime_mode='simulation'); second=svc.run(m,runtime_mode='simulation')
    assert first.imported_count==2 and first.failed_count==0 and repo.count()==2
    assert second.existing_count==2 and repo.count()==2
