from registries.nngla.spatial_realization.orchestration import GovernedSpatialBatchEngine
from registries.nngla.spatial_realization.persistence import MemorySpatialRealizationRepository
from registries.nngla.spatial_realization.topology import PassThroughTopologyEngine


def test_national_dry_assessment_uses_same_engine_for_all_major_cities():
    engine=GovernedSpatialBatchEngine(MemorySpatialRealizationRepository(),PassThroughTopologyEngine(),repository_revision='rev')
    preview=engine.assess_all_major_cities()
    assert preview.execution_ready
    assert len(preview.normalized_root_ids)==8
    assert len(preview.closures)==8
