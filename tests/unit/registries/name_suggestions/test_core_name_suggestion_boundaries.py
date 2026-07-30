from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
NEW_FILES=(ROOT/'registries'/'name_suggestions').glob('*.py')

def test_core_suggestions_do_not_couple_to_storage_or_future_domains():
    forbidden=('boto3','psycopg','sqlalchemy','supabase','citizen','email_candidate','random')
    for path in NEW_FILES:
        if path.name.startswith('manual_') or path.name=='__init__.py': continue
        text=path.read_text(encoding='utf-8').lower()
        for token in forbidden: assert token not in text, f'{token} leaked into {path.name}'
