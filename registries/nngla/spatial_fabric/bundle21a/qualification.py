from collections import Counter
from .source import current_candidates
from .eligibility import decide

def current_decisions(): return tuple(decide(c) for c in current_candidates())
def qualify_bundle():
    c=current_candidates(); d=current_decisions(); out=[]
    if len(c)!=1262: out.append(f'CANDIDATE_COUNT:{len(c)}')
    if Counter(x.record_family for x in c)!=Counter({'PLACE':700,'ADMINISTRATIVE_AREA':192,'ROAD':350,'GEOGRAPHIC_FEATURE':20}): out.append('FAMILY_COUNTS')
    if any(x.decision=='PUBLIC' for x in d): out.append('UNAUTHORIZED_PRELIVE_PUBLICATION')
    if any(x.publication_id for x in d): out.append('PUBLICATION_ID_WITHOUT_GATE')
    return tuple(out)
