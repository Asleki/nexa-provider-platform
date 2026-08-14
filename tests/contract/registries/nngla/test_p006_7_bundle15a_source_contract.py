import csv
from pathlib import Path
from registries.nngla.bundle15a_source import DEFAULT_SOURCE_ROOT, load_naming_statuses, load_gazette_actions

def test_bundle15a_source_snapshot_contains_real_governed_catalogues():
    catalogues=sorted((DEFAULT_SOURCE_ROOT/'04_name_catalogues').glob('*.csv'))
    assert len(catalogues)==18
    settlement=DEFAULT_SOURCE_ROOT/'04_name_catalogues'/'settlement_name_catalogue.csv'
    with settlement.open(encoding='utf-8-sig', newline='') as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==700
    assert all(r['source_dataset_id']=='dataset:novegeo:places:v001:700' for r in rows)

def test_naming_and_gazette_vocabulary_preserves_approval_publication_boundary():
    statuses={x.naming_status_code:x for x in load_naming_statuses()}
    assert statuses['PROPOSED'].requires_approval
    assert not statuses['PROPOSED'].can_display_publicly
    assert statuses['GAZETTED'].can_display_publicly
    actions={x.gazette_action_code:x for x in load_gazette_actions()}
    assert actions['NAME'].creates_legal_effect
    assert actions['RENAME'].creates_legal_effect
