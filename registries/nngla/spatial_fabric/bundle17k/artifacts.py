from ._shared import CANDIDATE_ROOT,EVIDENCE_ROOT
def artifact_paths():
 return {'geometry_changes':CANDIDATE_ROOT/'novegeo_geometry_change_candidates_v001.csv','supersession_links':CANDIDATE_ROOT/'novegeo_geometry_supersession_links_v001.csv','survey_observations':CANDIDATE_ROOT/'novegeo_survey_observation_candidates_v001.csv','survey_control_v002':CANDIDATE_ROOT/'survey_control_point_candidates_v002.csv','physical_state_changes':CANDIDATE_ROOT/'novegeo_physical_state_change_candidates_v001.csv','qualification_results':EVIDENCE_ROOT/'novegeo_geometry_change_qualification_results_v001.csv'}
__all__=['artifact_paths']
