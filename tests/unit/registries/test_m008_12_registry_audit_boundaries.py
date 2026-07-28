from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def test_registry_audit_has_no_parallel_repository_or_transport_imports():
    files=list((ROOT/'registries'/'audit').glob('*.py'))
    names={p.name for p in files}
    assert not any('repository' in name for name in names)
    text='\n'.join(p.read_text() for p in files)
    for forbidden in ('fastapi','flask','django','supabase','httpx','requests','zoho','openpyxl'):
        assert forbidden not in text.lower()
def test_prior_registry_tests_remain_present():
    tests=ROOT/'tests'/'unit'/'registries'
    for milestone in range(1,12):
        assert any(tests.glob(f'test_m008_{milestone}*'))
