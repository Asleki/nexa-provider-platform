from registries.nngla.spatial_fabric.bundle17j import load_schema17j_sql,qualify_schema17j_sql

def test_parcel_sql_uses_row_lock_idempotency_and_unique_ids():
 s=load_schema17j_sql(); assert qualify_schema17j_sql(s)==(); n=s.lower(); assert 'for update' in n and 'unique (parcel_id)' in n and 'unique (series_id, idempotency_key)' in n

def test_sql_is_host_agnostic_and_does_not_alter_locked_parcel():
 n=load_schema17j_sql().lower(); assert 'nexaecosystem.com' not in n and 'localhost' not in n and 'namecheap' not in n and 'alter table geography.nngla_parcel' not in n
