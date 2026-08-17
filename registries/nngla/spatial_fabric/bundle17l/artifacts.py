
from ._shared import RULES_PATH,TRANSITIONS_PATH,RECOGNITION_CANDIDATES_PATH,OBSERVATION_LINKS_PATH,RECOGNITION_RESULTS_PATH
def artifact_paths(): return {'qualification_rules':RULES_PATH,'lifecycle_transitions':TRANSITIONS_PATH,'recognition_candidates':RECOGNITION_CANDIDATES_PATH,'observation_links':OBSERVATION_LINKS_PATH,'recognition_results':RECOGNITION_RESULTS_PATH}
__all__=['artifact_paths']
