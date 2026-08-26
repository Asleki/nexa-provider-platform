from pathlib import Path
from registries.nngla.spatial_realization.closure import build_city_closure
from registries.nngla.spatial_realization.source import city_roots


def test_p006_7_11_15_5_is_additive_and_has_no_roadmap_or_locked_bundle_rewrite_dependency():
    root=Path(__file__).resolve().parents[3]
    package=root/'registries/nngla/spatial_realization'
    assert package.is_dir()
    text='\n'.join(path.read_text() for path in package.glob('*.py'))
    assert 'roadmap_frontend' not in text
    assert 'ST_SnapToGrid' not in text
    assert 'bundle19b/qualification.py' not in text


def test_all_eight_city_roots_have_automatic_execution_closure_without_name_specific_logic():
    for root in city_roots():
        closure=build_city_closure(root.place_id)
        assert closure.admin_root.subject_id==root.administrative_area_id
        assert len(closure.exhaustive_children)==8
        assert len(closure.regional_partition_peers)==4


def test_legacy_17p_worktree_lock_remains_future_compatible_with_additive_modules():
    root=Path(__file__).resolve().parents[3]
    lock=(root/'tests/registries/nngla/test_p006_7_11_7_20_operational_backend_lock.py').read_text()
    assert 'if status == "??"' in lock
    assert 'roadmap_names' in lock
    assert 'Locked production or roadmap surfaces changed during later additive work.' in lock
