from __future__ import annotations
from ._shared import ACCURACY_PATH,csv_rows

def accuracy_policy(code:str):
 rows={r['accuracy_class_code']:r for r in csv_rows(ACCURACY_PATH)}
 if code not in rows: raise ValueError('unknown governed survey accuracy class')
 return rows[code]
def qualify_survey_observation(observation):
 p=accuracy_policy(observation.accuracy_class_code); findings=[]
 if p['horizontal_accuracy_rule']!='PENDING_POLICY' or p['vertical_accuracy_rule']!='PENDING_POLICY': findings.append('unexpected-numeric-policy-state')
 if p['requires_instrument_record']=='true' and not observation.instrument_record_reference: findings.append('instrument-record-required')
 if p['requires_surveyor_approval']=='true' and not observation.surveyor_approval_reference: findings.append('surveyor-approval-required')
 return tuple(findings)
__all__=['accuracy_policy','qualify_survey_observation']
