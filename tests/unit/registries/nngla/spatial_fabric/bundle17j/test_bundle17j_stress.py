from registries.nngla.spatial_fabric.bundle17j import run_address_stress,run_address_display_stress,run_parcel_stress,run_site_stress,run_title_stress

def test_1000_parallel_address_ids_unique():
 r=run_address_stress(1000); assert r.successful_count==1000 and r.duplicate_identity_count==0

def test_1000_parallel_address_display_numbers_unique_within_scope():
 r=run_address_display_stress(1000); assert r.unique_identity_count==1000 and r.collision_count==0

def test_1000_parallel_parcel_refs_unique():
 r=run_parcel_stress(1000); assert r.unique_identity_count==1000 and r.duplicate_identity_count==0

def test_1000_parallel_site_ids_unique():
 r=run_site_stress(1000); assert r.unique_identity_count==1000

def test_1000_parallel_title_refs_unique():
 r=run_title_stress(1000); assert r.unique_identity_count==1000
