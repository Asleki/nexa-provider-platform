from pathlib import Path
from registries.nngla.spatial_realization.closure import build_city_closure
from registries.nngla.spatial_realization.contracts import DependencyRole
from registries.nngla.spatial_realization.source import city_roots


def test_every_major_city_resolves_same_generic_dependency_shape_from_source():
    for root in city_roots():
        closure=build_city_closure(root.place_id)
        assert closure.root==root
        assert len(closure.exhaustive_children)==8
        assert len(closure.overlays)==1
        assert len(closure.regional_partition_peers)==4
        assert closure.validation_parent.subject_id==root.validation_parent_id
        assert closure.place_reference.subject_id==root.place_id
        assert closure.supporting_spatial_point_id.startswith('NG-SPT-')
        assert sum(d.role is DependencyRole.EXHAUSTIVE_CHILD for d in closure.dependencies)==8


def test_engine_closure_contains_no_orivane_specific_branch():
    text=Path('registries/nngla/spatial_realization/closure.py').read_text()
    assert 'if root_place_id == "NG-PLC-000001"' not in text
    assert 'if canonical_name == "Orivane"' not in text


def test_every_exhaustive_child_has_one_canonical_spatial_seed():
    for root in city_roots():
        closure=build_city_closure(root.place_id)
        assert len(closure.exhaustive_child_seeds)==len(closure.exhaustive_children)==8
        assert {s.subject_id for s in closure.exhaustive_child_seeds}=={c.subject_id for c in closure.exhaustive_children}
        assert all(s.source_place_code.startswith('NGP-') and s.place_id.startswith('NG-PLC-') for s in closure.exhaustive_child_seeds)
        assert all(-180<=s.longitude<=180 and -90<=s.latitude<=90 for s in closure.exhaustive_child_seeds)
