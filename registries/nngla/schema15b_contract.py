"""Additive P006.7.5/P006.7.6 PostgreSQL/PostGIS schema-extension contract."""
from pathlib import Path
SCHEMA15B_SQL=Path(__file__).resolve().parents[2]/'database'/'schemas'/'nngla_geometry_roads_addresses.sql'
REQUIRED_15B_TABLES=(
 'geography.nngla_geometry_authority_record',
 'geography.nngla_survey_record',
 'geography.nngla_survey_control_point',
 'geography.nngla_road_reference_candidate',
 'geography.nngla_road',
 'geography.nngla_addressable_site',
 'geography.nngla_address',
)
def load_schema15b_sql(path=SCHEMA15B_SQL): return Path(path).read_text(encoding='utf-8')
def qualify_schema15b_sql(sql):
    n=sql.lower(); findings=[]
    for t in REQUIRED_15B_TABLES:
        if f'create table {t}' not in n: findings.append(f'missing:{t}')
    for token in ('geometry_id','accuracy_class_code','road_candidate_id','road_id','site_id','address_id','parcel_id','runtime_effect_scope'):
        if token not in n: findings.append(f'missing-column:{token}')
    if 'create extension' in n: findings.append('bundle15b-must-reuse-locked-postgis-foundation')
    if 'migration_manifest' in n: findings.append('schema-extension-must-not-register-locked-migration-manifest')
    return tuple(findings)
__all__=['SCHEMA15B_SQL','REQUIRED_15B_TABLES','load_schema15b_sql','qualify_schema15b_sql']
