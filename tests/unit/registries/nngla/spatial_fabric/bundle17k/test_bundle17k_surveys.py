from registries.nngla.spatial_fabric.bundle17k import *

def test_survey_accuracy_thresholds_remain_pending_policy():
 p=accuracy_policy('CADASTRAL_SURVEY'); assert p['horizontal_accuracy_rule']=='PENDING_POLICY' and p['vertical_accuracy_rule']=='PENDING_POLICY'
def test_cadastral_survey_requires_instrument_and_approval_without_inventing_numeric_tolerance():
 o=form_survey_observation(survey_id='NG-SRV-000001',subject_id='NV-01-001-0001',observed_at='2026-08-17T00:00:00Z',longitude=35,latitude=-1,accuracy_class_code='CADASTRAL_SURVEY',source_reference='test')
 assert set(qualify_survey_observation(o))=={'instrument-record-required','surveyor-approval-required'}
 o2=form_survey_observation(survey_id='NG-SRV-000001',subject_id='NV-01-001-0001',observed_at='2026-08-17T00:00:00Z',longitude=35,latitude=-1,accuracy_class_code='CADASTRAL_SURVEY',source_reference='test',instrument_record_reference='instrument:1',surveyor_approval_reference='surveyor:1')
 assert qualify_survey_observation(o2)==()
