"""P006.7.7/P006.7.8 end-to-end Bundle 15C qualification."""
from __future__ import annotations
from dataclasses import dataclass
from .bundle15c_source import load_land_use_codes,load_tenure_types,load_title_types,load_state_land_categories,load_parcel_bootstrap,load_title_bootstrap,load_state_land_bootstrap
from .schema15c_contract import load_schema15c_sql,qualify_schema15c_sql
QUALIFICATION_ID='qualification:novegeo:nngla-bundle15c:v1'

@dataclass(frozen=True,slots=True)
class Bundle15CQualificationReceipt:
    qualification_id:str
    status:str
    findings:tuple[str,...]
    land_use_count:int
    tenure_type_count:int
    title_type_count:int
    state_land_category_count:int
    parcel_bootstrap_count:int
    title_bootstrap_count:int
    state_land_bootstrap_count:int

def qualify_bundle15c():
    land=load_land_use_codes(); tenures=load_tenure_types(); titles=load_title_types(); statecats=load_state_land_categories()
    parcels=load_parcel_bootstrap(); title_records=load_title_bootstrap(); state_records=load_state_land_bootstrap(); findings=[]
    if len(land)!=13: findings.append(f'land-use-count:{len(land)}')
    if len(tenures)!=7: findings.append(f'tenure-type-count:{len(tenures)}')
    if len(titles)!=6: findings.append(f'title-type-count:{len(titles)}')
    if len(statecats)!=6: findings.append(f'state-land-category-count:{len(statecats)}')
    if parcels: findings.append(f'parcel-bootstrap-must-remain-empty:{len(parcels)}')
    if title_records: findings.append(f'title-bootstrap-must-remain-empty:{len(title_records)}')
    if state_records: findings.append(f'state-land-bootstrap-must-remain-empty:{len(state_records)}')
    tenure_codes={x.tenure_type_code for x in tenures}
    unknown=sorted({x.tenure_type_code for x in titles}-tenure_codes)
    if unknown: findings.append('title-types-reference-unknown-tenure:'+','.join(unknown))
    if not all(x.requires_parcel for x in titles): findings.append('day-zero-title-types-must-require-parcel')
    if 'JOINT' not in tenure_codes or 'JOINT_TITLE' not in {x.title_type_code for x in titles}: findings.append('joint-tenure-extension-point-missing')
    findings.extend(qualify_schema15c_sql(load_schema15c_sql()))
    return Bundle15CQualificationReceipt(QUALIFICATION_ID,'QUALIFIED' if not findings else 'FAILED',tuple(findings),len(land),len(tenures),len(titles),len(statecats),len(parcels),len(title_records),len(state_records))

__all__=['QUALIFICATION_ID','Bundle15CQualificationReceipt','qualify_bundle15c']
