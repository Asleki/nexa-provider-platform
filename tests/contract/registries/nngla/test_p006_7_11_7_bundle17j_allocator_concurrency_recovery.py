from registries.nngla.spatial_fabric.bundle17j import bundle17j_is_qualified,geometry_namespace_baseline,run_address_stress,run_address_display_stress,run_parcel_stress,run_site_stress,run_title_stress,load_schema17j_sql,qualify_schema17j_sql

def test_bundle17j_contract_attacks_all_17g_17h_17i_allocator_families_at_1000():
 rows=(run_address_stress(1000),run_address_display_stress(1000),run_parcel_stress(1000),run_site_stress(1000),run_title_stress(1000)); assert all(r.requested_count==1000 and r.unique_identity_count==1000 and r.duplicate_identity_count==0 for r in rows)
def test_bundle17j_geometry_guard_protects_existing_2432_allocations():
 b=geometry_namespace_baseline(); assert b['max_geometry_id']=='NG-GEO-002432' and b['next_candidate_id']=='NG-GEO-002433'
def test_bundle17j_postgresql_parcel_contract_closes_17g_database_concurrency_deferral_without_touching_locked_table():
 assert qualify_schema17j_sql(load_schema17j_sql())==(); assert bundle17j_is_qualified()
