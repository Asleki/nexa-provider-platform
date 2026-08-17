from __future__ import annotations
from ._shared import ACCURACY_PATH,csv_rows,stable_id
from .contracts import SurveyObservationCandidate

def governed_accuracy_classes(): return tuple(r['accuracy_class_code'] for r in csv_rows(ACCURACY_PATH))
def form_survey_observation(*,survey_id,subject_id,observed_at,longitude,latitude,accuracy_class_code,source_reference,elevation_m='',instrument_record_reference='',surveyor_approval_reference=''):
 if accuracy_class_code not in governed_accuracy_classes(): raise ValueError('unknown governed survey accuracy class')
 oid=stable_id('surveyobs:nngla:',survey_id,subject_id,observed_at,longitude,latitude,source_reference)
 return SurveyObservationCandidate(oid,survey_id,subject_id,observed_at,float(longitude),float(latitude),str(elevation_m),'NG-CRS-EPSG4326',accuracy_class_code,instrument_record_reference,surveyor_approval_reference,source_reference,'CANDIDATE')
__all__=['governed_accuracy_classes','form_survey_observation']
