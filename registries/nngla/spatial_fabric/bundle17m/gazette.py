
from __future__ import annotations
from ._shared import GAZETTE_ACTION_PATH,GAZETTE_CANDIDATES_PATH,csv_rows,stable_id
from .contracts import GazetteActionCandidate

def gazette_action_codes(): return frozenset(r['gazette_action_code'] for r in csv_rows(GAZETTE_ACTION_PATH) if r['status']=='ACTIVE')
def gazette_candidates(): return tuple(GazetteActionCandidate(r['candidate_id'],r['subject_id'],r['name_id'],r['gazette_action_code'],r['prior_name_id'],r['proposed_effective_on'],r['proposer_reference'],r['decision_reference'],r['runtime_mode'],r['candidate_status']) for r in csv_rows(GAZETTE_CANDIDATES_PATH))
def form_gazette_candidate(*,subject_id,name_id,gazette_action_code,proposed_effective_on,proposer_reference='',decision_reference='',prior_name_id='',runtime_mode='simulation'):
    if gazette_action_code not in gazette_action_codes(): raise ValueError('unknown governed gazette action')
    return GazetteActionCandidate(stable_id('gazettecand:nngla:',subject_id,name_id,gazette_action_code,proposed_effective_on),subject_id,name_id,gazette_action_code,prior_name_id,proposed_effective_on,proposer_reference,decision_reference,runtime_mode,'CANDIDATE')
__all__=['gazette_action_codes','gazette_candidates','form_gazette_candidate']
