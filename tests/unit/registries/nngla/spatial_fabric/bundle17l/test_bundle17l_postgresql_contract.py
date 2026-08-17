
from registries.nngla.spatial_fabric.bundle17l import load_schema17l_sql,qualify_schema17l_sql

def test_schema_is_additive_host_agnostic_and_uses_existing_canonical_feature_table(): assert qualify_schema17l_sql(load_schema17l_sql())==()
