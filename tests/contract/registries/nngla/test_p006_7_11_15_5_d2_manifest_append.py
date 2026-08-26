import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]


def test_delivery2_manifest_entry_matches_exact_artifacts():
    root=ROOT/'database/migrations'; data=json.loads((root/'migration_manifest.json').read_text())
    row=[x for x in data['migrations'] if x['migration_id']=='m006_07_11_nngla_shared_face_candidate_lifecycle']
    assert len(row)==1 and row[0]['sequence_number']==21 and row[0]['destructive'] is False
    row=row[0]
    for side in ('forward','rollback'):
        p=root/row[f'{side}_file']
        assert hashlib.sha256(p.read_bytes()).hexdigest()==row[f'{side}_sha256']
        assert p.stat().st_size==row[f'{side}_byte_size']
