from registries.nngla.spatial_fabric.bundle19b.artifacts import missing_artifacts
from registries.nngla.spatial_fabric.bundle19b.materialize import materialization_summary
def test_materialized_artifacts_exist_and_summary_is_exact():
 assert missing_artifacts()==(); s=materialization_summary(); assert s['administrative_identity_count']==192 and s['qualified_count']==192 and s['legalization_approved_count']==192; assert s['illegal_overlap_findings']==0 and s['gap_findings']==0 and s['schema_migration_required'] is False
