from registries.nngla.spatial_fabric.bundle17k import load_schema17k_sql,qualify_schema17k_sql

def test_sql_allocates_from_authoritative_occupied_namespace_and_uses_row_lock():
 s=load_schema17k_sql(); assert qualify_schema17k_sql(s)==(); n=s.lower(); assert 'nngla_geometry_version' in n and 'nngla_geometry_authority_record' in n and 'for update' in n
def test_sql_is_host_agnostic_and_no_destructive_geometry_payload_update():
 n=load_schema17k_sql().lower(); assert all(x not in n for x in ('nexaecosystem.com','localhost','namecheap')); assert 'update geography.nngla_geometry_version set geometry=' not in n
