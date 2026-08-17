
from __future__ import annotations
from ._shared import TRANSITIONS_PATH,csv_rows,bool_text
from .contracts import FeatureLifecycleTransition

def lifecycle_transitions(): return tuple(FeatureLifecycleTransition(r['transition_id'],r['from_status'],r['to_status'],bool_text(r['requires_production_authority']),bool_text(r['retains_feature_identity']),bool_text(r['terminal_transition']),r['status']) for r in csv_rows(TRANSITIONS_PATH))
def transition_allowed(from_status,to_status,*,runtime_mode='production'):
    for t in lifecycle_transitions():
        if t.from_status==from_status and t.to_status==to_status:
            return not t.requires_production_authority or runtime_mode=='production'
    return False
__all__=['lifecycle_transitions','transition_allowed']
