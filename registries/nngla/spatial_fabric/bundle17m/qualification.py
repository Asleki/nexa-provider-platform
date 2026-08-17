
from __future__ import annotations
from collections import Counter
from .name_families import name_families,load_family_catalogue,governed_name_count
from .assignments import assignment_rules,existing_assignment_candidates,assignment_results
from .lifecycle import naming_status_codes
from .gazette import gazette_candidates
from .postgresql_contract import load_schema17m_sql,qualify_schema17m_sql
from ._shared import normalize_name_text

def cross_family_duplicate_count():
    by_text={}
    for f in name_families():
        for r in load_family_catalogue(f.name_family_code):
            by_text.setdefault(normalize_name_text(r['canonical_name']),set()).add(f.name_family_code)
    return sum(1 for families in by_text.values() if len(families)>1)
def bundle17m_is_qualified():
    fam=name_families(); rules=assignment_rules(); assignments=existing_assignment_candidates(); results=assignment_results(); statuses=naming_status_codes()
    return len(fam)==19 and governed_name_count()==6240 and len(rules)==19 and len(assignments)==20 and len(results)==20 and all(r.result_status=='PRESERVED_PROPOSED_UNGAZETTED' and not r.official_effect for r in results) and len(gazette_candidates())==0 and {'AVAILABLE','PROPOSED','APPROVED','GAZETTED','ACTIVE_OFFICIAL','HISTORIC'}<=statuses and cross_family_duplicate_count()==63 and qualify_schema17m_sql(load_schema17m_sql())==()
__all__=['cross_family_duplicate_count','bundle17m_is_qualified']
