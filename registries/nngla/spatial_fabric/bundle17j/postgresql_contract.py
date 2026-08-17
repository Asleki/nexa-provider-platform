from __future__ import annotations
from ._shared import SCHEMA_PATH
def load_schema17j_sql(): return SCHEMA_PATH.read_text(encoding='utf-8')
def qualify_schema17j_sql(sql:str):
    n=sql.lower(); findings=[]
    for token in ('create table geography.nngla_parcel_reference_series','create table geography.nngla_parcel_reference_reservation','create or replace function geography.nngla_reserve_parcel_reference','for update','unique (parcel_id)','unique (series_id, idempotency_key)','monotonic_no_reuse'):
        if token not in n: findings.append(f'missing-sql:{token}')
    for forbidden in ('nexaecosystem.com','localhost','namecheap'):
        if forbidden in n: findings.append(f'forbidden-coupling:{forbidden}')
    if 'alter table geography.nngla_parcel' in n: findings.append('locked-parcel-table-alteration')
    return tuple(findings)
__all__=['load_schema17j_sql','qualify_schema17j_sql']
