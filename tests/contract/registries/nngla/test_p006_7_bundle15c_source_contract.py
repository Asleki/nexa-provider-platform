from pathlib import Path
import hashlib,json
from registries.nngla.bundle15c_source import DEFAULT_SOURCE_ROOT,load_land_use_codes,load_tenure_types,load_title_types,load_state_land_categories,load_parcel_bootstrap,load_title_bootstrap,load_state_land_bootstrap

def test_bundle15c_source_snapshot_contains_complete_governed_land_vocabularies_and_empty_legal_registers():
    assert len(load_land_use_codes())==13
    assert len(load_tenure_types())==7
    assert len(load_title_types())==6
    assert len(load_state_land_categories())==6
    assert load_parcel_bootstrap()==()
    assert load_title_bootstrap()==()
    assert load_state_land_bootstrap()==()

def test_bundle15c_provenance_hashes_match_every_copied_governed_csv():
    root=DEFAULT_SOURCE_ROOT.parent
    doc=json.loads((root/'provenance'/'bundle15c_authority_source.json').read_text())
    assert len(doc['files'])==7
    for item in doc['files']:
        p=root/item['path']
        assert p.is_file()
        assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256']

def test_land_bootstrap_registers_have_governed_headers_without_placeholder_rows():
    expected={
      'parcel_bootstrap.csv':'parcel_id,parent_parcel_id,cadastral_series,parcel_sequence,parcel_status,geometry_reference,land_use_code,survey_status,created_effective_at,retired_effective_at,source_reference',
      'title_bootstrap.csv':'title_id,parcel_id,title_type_code,tenure_type_code,holder_reference,title_status,effective_from,effective_to,source_reference',
      'state_land_bootstrap.csv':'state_land_record_id,parcel_id,state_land_category_code,administrative_area_id,status,effective_from,effective_to,source_reference',
    }
    for name,header in expected.items():
        lines=(DEFAULT_SOURCE_ROOT/'07_land'/name).read_text(encoding='utf-8-sig').splitlines()
        assert lines==[header]
