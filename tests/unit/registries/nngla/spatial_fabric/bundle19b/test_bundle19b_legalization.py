from registries.nngla.spatial_fabric.bundle19b.legalization import load_legalization_decisions
def test_all_192_boundaries_have_explicit_initial_legalization_decisions():
 rows=load_legalization_decisions(); assert len(rows)==192; assert all(r['decision_status']=='APPROVED_FOR_GOVERNED_LIVE_APPLICATION' for r in rows); assert all(r['resulting_boundary_status']=='LEGALIZED' and r['resulting_lifecycle_status']=='ACTIVE' for r in rows)
