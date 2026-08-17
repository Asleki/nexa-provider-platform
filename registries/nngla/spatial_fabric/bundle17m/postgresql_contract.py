
from ._shared import SCHEMA_PATH
def load_schema17m_sql(): return SCHEMA_PATH.read_text(encoding='utf-8')
def qualify_schema17m_sql(sql):
    n=sql.lower(); compact=''.join(n.split()); findings=[]
    for token in ('create table geography.nngla_name_family_policy','create table geography.nngla_name_id_reservation','create table geography.nngla_name_lifecycle_event','create table geography.nngla_gazette_action_candidate','create table geography.nngla_name_assignment_result','create or replace function geography.nngla_reserve_name_id','for update','nngla_geographic_name','nngla_name_assignment'):
        if token not in n:findings.append('missing-sql:'+token)
    if 'unique(name_family_code,normalized_match_key,scope_type,scope_reference)' not in compact:findings.append('missing-sql:scoped-name-uniqueness')
    for bad in ('nexaecosystem.com','localhost','namecheap'):
        if bad in n:findings.append('forbidden-coupling:'+bad)
    if 'alter table geography.nngla_geographic_name' in n or 'alter table geography.nngla_name_assignment' in n:findings.append('locked-name-table-alteration')
    return tuple(findings)
__all__=['load_schema17m_sql','qualify_schema17m_sql']
