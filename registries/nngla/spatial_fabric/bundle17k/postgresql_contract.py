from ._shared import SCHEMA_PATH
def load_schema17k_sql(): return SCHEMA_PATH.read_text(encoding='utf-8')
def qualify_schema17k_sql(sql):
 n=sql.lower(); findings=[]
 for token in ('create table geography.nngla_geometry_id_allocator','create table geography.nngla_geometry_id_reservation','create table geography.nngla_geometry_change_candidate','create table geography.nngla_geometry_supersession_link','create table geography.nngla_survey_observation_candidate','create table geography.nngla_physical_state_change_candidate','create or replace function geography.nngla_reserve_geometry_id','for update','nngla_geometry_version','nngla_geometry_authority_record'):
  if token not in n:findings.append('missing-sql:'+token)
 for bad in ('nexaecosystem.com','localhost','namecheap'):
  if bad in n:findings.append('forbidden-coupling:'+bad)
 if 'update geography.nngla_geometry_version set geometry=' in n: findings.append('destructive-geometry-replacement')
 return tuple(findings)
__all__=['load_schema17k_sql','qualify_schema17k_sql']
