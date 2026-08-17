
from __future__ import annotations
from ._shared import TRANSITIONS_PATH,NAMING_STATUS_PATH,csv_rows,bool_text
from .contracts import NameLifecycleTransition

def naming_status_codes(): return frozenset(r['naming_status_code'] for r in csv_rows(NAMING_STATUS_PATH))
def lifecycle_transitions(): return tuple(NameLifecycleTransition(r['transition_id'],r['from_status'],r['to_status'],bool_text(r['requires_approval']),bool_text(r['requires_gazette']),bool_text(r['creates_legal_effect']),bool_text(r['terminal_transition']),r['status']) for r in csv_rows(TRANSITIONS_PATH))
def transition_allowed(from_status,to_status,*,approved=False,gazetted=False):
    for t in lifecycle_transitions():
        if t.from_status==from_status and t.to_status==to_status:return (not t.requires_approval or approved) and (not t.requires_gazette or gazetted)
    return False
__all__=['naming_status_codes','lifecycle_transitions','transition_allowed']
