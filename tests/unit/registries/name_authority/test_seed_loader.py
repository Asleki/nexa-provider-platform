import json,hashlib
from pathlib import Path
import pytest
from registries.name_authority import ProductionSeedLoader,SeedIntegrityError,SeedPathError

def build(tmp_path, content='id,name\n1,Ada\n'):
    (tmp_path/'x.csv').write_text(content,encoding='utf-8')
    sha=hashlib.sha256((tmp_path/'x.csv').read_bytes()).hexdigest()
    data={"manifest_schema":"npp.production-seed-manifest","manifest_schema_version":1,"classification":"production_seed","status":"approved","encoding":"utf-8","delimiter":",","runtime_policy":{"eligible_runtime_modes":["simulation","production"]},"governance":{"direct_sql_import_allowed":False,"postgresql_copy_allowed":False,"python_validation_required":True},"dataset_id":"dataset.test","dataset_version":1,"dataset_name":"Test","domain":"name_catalogue","source_family":"test","files":[{"file_id":"file.test","path":"x.csv","record_role":"atomic_name","required_headers":["id","name"],"row_count":1,"sha256":sha,"import_enabled":True,"target_name_kind":"first_name","column_mappings":{"id":"external_record_id","name":"raw_name_value"}}]}
    (tmp_path/'manifest.json').write_text(json.dumps(data),encoding='utf-8'); return data

def test_loads_and_validates_manifest_file(tmp_path):
    build(tmp_path); loader=ProductionSeedLoader(tmp_path); m=loader.load_manifest(tmp_path/'manifest.json'); report=loader.validate(m)
    assert m.dataset_id=='dataset.test' and report.files[0].row_count==1 and loader.validate_runtime(m,' PRODUCTION ')=='production'

def test_rejects_checksum_mismatch_and_path_escape(tmp_path):
    data=build(tmp_path); data['files'][0]['sha256']='0'*64; (tmp_path/'manifest.json').write_text(json.dumps(data))
    loader=ProductionSeedLoader(tmp_path); m=loader.load_manifest(tmp_path/'manifest.json')
    with pytest.raises(SeedIntegrityError): loader.validate(m)
    with pytest.raises(SeedPathError): loader._safe('../secret')

def test_bom_headers_are_read_safely(tmp_path):
    build(tmp_path,'\ufeffid,name\n1,José\n'); loader=ProductionSeedLoader(tmp_path); m=loader.load_manifest(tmp_path/'manifest.json')
    assert loader.validate(m).files[0].headers==('id','name')
