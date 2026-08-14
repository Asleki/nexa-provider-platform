from pathlib import Path
import hashlib,json,csv
from registries.nngla.bundle15b_source import DEFAULT_SOURCE_ROOT,load_geometry_versions,load_survey_control_points,load_road_candidates,load_address_candidates

def test_bundle15b_source_snapshot_counts_and_empty_registers_are_preserved():
    assert len(load_geometry_versions())==21
    assert load_survey_control_points()==()
    assert len(load_road_candidates())==900
    assert load_address_candidates()==()

def test_bundle15b_provenance_hashes_match_every_copied_governed_csv():
    provenance=DEFAULT_SOURCE_ROOT.parent/'provenance'/'bundle15b_authority_source.json'
    payload=json.loads(provenance.read_text(encoding='utf-8'))
    assert payload['copy_policy']=='BYTE_EXACT_GOVERNED_SOURCE_SNAPSHOT'
    assert len(payload['files'])==8
    for item in payload['files']:
        path=DEFAULT_SOURCE_ROOT/item['relative_path']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256']
        with path.open(encoding='utf-8-sig',newline='') as f: assert sum(1 for _ in csv.DictReader(f))==item['row_count']

def test_empty_registers_have_real_governed_headers_not_placeholder_rows():
    for rel in ('05_geographic_candidates/survey_control_point_candidates.csv','06_roads_addresses/address_reference_candidates.csv'):
        lines=(DEFAULT_SOURCE_ROOT/rel).read_text(encoding='utf-8-sig').splitlines()
        assert len(lines)==1 and ',' in lines[0]
