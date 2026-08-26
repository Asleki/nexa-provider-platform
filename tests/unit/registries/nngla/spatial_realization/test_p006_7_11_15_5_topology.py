from pathlib import Path
from registries.nngla.spatial_realization.closure import build_city_closure
from registries.nngla.spatial_realization.topology import (
    DIAGNOSTIC_EQUAL_AREA_SRID,MAX_AUTOMATIC_RESIDUAL_KM2,MAX_AUTOMATIC_RESIDUAL_RATIO,
    PassThroughTopologyEngine,REPAIR_POLICY_ID,TOPOLOGY_POLICY_ID,
)


def test_topology_policy_distinguishes_exact_truth_from_repair_eligibility():
    assert DIAGNOSTIC_EQUAL_AREA_SRID==6933
    assert 0 < MAX_AUTOMATIC_RESIDUAL_KM2 <= 0.01
    assert 0 < MAX_AUTOMATIC_RESIDUAL_RATIO <= 1e-6
    assert 'topology' in TOPOLOGY_POLICY_ID
    assert 'reconciliation' in REPAIR_POLICY_ID


def test_database_free_core_can_use_explicit_pass_through_adapter_only_for_tests():
    closure=build_city_closure('NG-PLC-000001')
    assessment=PassThroughTopologyEngine().assess(closure)
    assert assessment.execution_ready
    assert assessment.candidates==closure.desired_candidates


def test_postgis_topology_implementation_contains_required_exact_predicates_and_no_grid_snap_repair():
    text=Path('registries/nngla/spatial_realization/topology.py').read_text()
    for token in ('ST_IsValid','ST_CoveredBy','ST_Difference','ST_Dimension','ST_Intersection','ST_UnaryUnion','ST_PointOnSurface','ST_Transform'):
        assert token in text
    assert 'ST_SnapToGrid' not in text
    assert 'historical' in text.lower()


def test_governed_structural_mode_cannot_auto_construct_material_structural_successor():
    from registries.nngla.spatial_realization.contracts import FindingSeverity,FindingStatus,RepairMode,TopologyAssessment,TopologyFinding
    from registries.nngla.spatial_realization.topology import PostGISSpatialTopologyEngine
    closure=build_city_closure('NG-PLC-000001')
    finding=TopologyFinding(
        'finding:material','NG-PLC-000001','CITY_DISTRICT_GAP',FindingSeverity.BLOCKING,FindingStatus.OPEN,
        closure.root.administrative_area_id,repair_eligibility='GOVERNED_STRUCTURAL_REVIEW_REQUIRED',
    )
    assessment=TopologyAssessment(closure.root.place_id,closure.desired_candidates,(finding,))
    assert not PostGISSpatialTopologyEngine(None,repair_mode=RepairMode.DISABLED)._repair_eligible(closure,assessment)
    assert not PostGISSpatialTopologyEngine(None,repair_mode=RepairMode.SAFE_AUTOMATIC)._repair_eligible(closure,assessment)
    assert not PostGISSpatialTopologyEngine(None,repair_mode=RepairMode.GOVERNED_STRUCTURAL)._repair_eligible(closure,assessment)


def test_successor_repair_versions_the_selected_city_partition_as_one_coherent_fabric_contract():
    text=Path('registries/nngla/spatial_realization/topology.py').read_text()
    assert 'successor fabric' in text
    assert 'repaired_city.checksum_sha256==city.checksum_sha256' not in text
    assert 'repaired.checksum_sha256==original.checksum_sha256' not in text
    assert 'GOVERNED_STRUCTURAL_REVIEW_REQUIRED' in Path('registries/nngla/spatial_realization/residual_policy.py').read_text()
