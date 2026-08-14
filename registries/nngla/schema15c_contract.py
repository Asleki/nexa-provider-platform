"""Additive P006.7.7/P006.7.8 PostgreSQL schema-extension contract."""
from pathlib import Path
SCHEMA15C_SQL=Path(__file__).resolve().parents[2]/'database'/'schemas'/'nngla_cadastre_titles_state_land.sql'
REQUIRED_15C_TABLES=(
 'geography.nngla_parcel',
 'geography.nngla_parcel_lineage',
 'geography.nngla_parcel_lineage_member',
 'geography.nngla_cadastral_geometry_assignment',
 'geography.nngla_title',
 'geography.nngla_state_land',
)
def load_schema15c_sql(path=SCHEMA15C_SQL): return Path(path).read_text(encoding='utf-8')
def qualify_schema15c_sql(sql):
    n=sql.lower(); findings=[]
    for t in REQUIRED_15C_TABLES:
        if f'create table {t}' not in n: findings.append(f'missing:{t}')
    for token in ('parcel_id','parent_parcel_id','geometry_reference','land_use_code','survey_status','title_id','title_type_code','tenure_type_code','holder_reference','state_land_record_id','state_land_category_code','runtime_effect_scope'):
        if token not in n: findings.append(f'missing-column:{token}')
    if 'create extension' in n: findings.append('bundle15c-must-reuse-locked-postgis-foundation')
    if 'migration_manifest' in n: findings.append('schema-extension-must-not-register-locked-migration-manifest')
    for forbidden in ('soko','nre-','listing_id','property_price'):
        if forbidden in n: findings.append(f'consumer-domain-leak:{forbidden}')
    return tuple(findings)
__all__=['SCHEMA15C_SQL','REQUIRED_15C_TABLES','load_schema15c_sql','qualify_schema15c_sql']
