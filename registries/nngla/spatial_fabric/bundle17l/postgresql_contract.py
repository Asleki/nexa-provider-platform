
from ._shared import SCHEMA_PATH
def load_schema17l_sql(): return SCHEMA_PATH.read_text(encoding='utf-8')
def qualify_schema17l_sql(sql):
    n=sql.lower(); findings=[]
    for token in ('create table geography.nngla_feature_id_allocator','create table geography.nngla_feature_id_reservation','create table geography.nngla_feature_runtime_candidate','create table geography.nngla_feature_candidate_observation','create table geography.nngla_feature_recognition_result','create table geography.nngla_feature_lifecycle_event','create or replace function geography.nngla_reserve_feature_id','for update','nngla_spatial_feature','nngla_canonical_crosswalk'):
        if token not in n:findings.append('missing-sql:'+token)
    for bad in ('nexaecosystem.com','localhost','namecheap'):
        if bad in n:findings.append('forbidden-coupling:'+bad)
    if 'alter table geography.nngla_spatial_feature' in n:findings.append('locked-feature-table-alteration')
    return tuple(findings)
__all__=['load_schema17l_sql','qualify_schema17l_sql']
