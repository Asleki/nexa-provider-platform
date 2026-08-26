from registries.nngla.spatial_realization.closure import build_city_closure
from registries.nngla.spatial_realization.contracts import (
    AssessmentStage,FindingSeverity,FindingStatus,RepairMode,TopologyAssessment,TopologyFinding,
)
from registries.nngla.spatial_realization.topology import PostGISSpatialTopologyEngine,REPAIR_POLICY_ID,TOPOLOGY_POLICY_ID


class StageEngine(PostGISSpatialTopologyEngine):
    def __init__(self,successor_blocked=False):
        super().__init__(None,repair_mode=RepairMode.SAFE_AUTOMATIC)
        self.successor_blocked=successor_blocked
    def _assess_once(self,closure,candidates,*,stage):
        if stage is AssessmentStage.SOURCE_CANDIDATE:
            finding=TopologyFinding(
                'finding:source',closure.root.place_id,'CITY_DISTRICT_GAP',FindingSeverity.BLOCKING,FindingStatus.OPEN,
                closure.root.administrative_area_id,assessment_stage=stage,repair_eligibility='AUTOMATIC_SUCCESSOR_ELIGIBLE',repair_strategy=REPAIR_POLICY_ID,
            )
            return TopologyAssessment(closure.root.place_id,candidates,(finding,))
        if self.successor_blocked:
            finding=TopologyFinding(
                'finding:successor',closure.root.place_id,'CITY_DISTRICT_GAP',FindingSeverity.BLOCKING,FindingStatus.OPEN,
                closure.root.administrative_area_id,assessment_stage=stage,repair_eligibility='GOVERNED_STRUCTURAL_REVIEW_REQUIRED',
            )
            return TopologyAssessment(closure.root.place_id,candidates,(finding,))
        return TopologyAssessment(closure.root.place_id,candidates,())
    def _repair_selected_fabric(self,closure,originals):
        return originals


def test_source_blockers_become_superseded_provenance_after_successor_reverification():
    closure=build_city_closure('NG-PLC-000001')
    assessment=StageEngine().assess(closure)
    assert assessment.execution_ready
    source=next(f for f in assessment.findings if f.finding_id=='finding:source')
    assert source.status is FindingStatus.SUPERSEDED
    assert any(f.assessment_stage is AssessmentStage.SUCCESSOR_CANDIDATE for f in assessment.findings)


def test_successor_blocker_not_source_history_gates_execution():
    closure=build_city_closure('NG-PLC-000001')
    assessment=StageEngine(successor_blocked=True).assess(closure)
    assert not assessment.execution_ready
    assert next(f for f in assessment.findings if f.finding_id=='finding:source').status is FindingStatus.SUPERSEDED
    assert next(f for f in assessment.findings if f.finding_id=='finding:successor').blocking


def test_r3_policy_versions_invalidate_r2_authorization_semantics():
    from registries.nngla.spatial_realization.preview import PLAN_VERSION
    assert PLAN_VERSION==2
    assert TOPOLOGY_POLICY_ID.endswith('-v2')
    assert REPAIR_POLICY_ID.endswith('-v2')
