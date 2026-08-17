
from registries.nngla.spatial_fabric.bundle17m import load_schema17m_sql,qualify_schema17m_sql

def test_schema_extends_existing_name_tables_without_domain_or_host_coupling(): assert qualify_schema17m_sql(load_schema17m_sql())==()
