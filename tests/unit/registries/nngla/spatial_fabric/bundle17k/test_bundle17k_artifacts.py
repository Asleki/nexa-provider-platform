from csv import DictReader
from registries.nngla.spatial_fabric.bundle17k import artifact_paths
from registries.nngla.spatial_fabric.bundle17k._shared import DAY_ZERO_CONTROL_PATH,csv_rows

def test_day_zero_survey_control_remains_empty_and_v002_is_additive():
 p=artifact_paths(); assert csv_rows(DAY_ZERO_CONTROL_PATH)==() and csv_rows(p['survey_control_v002'])==()
def test_required_artifacts_exist_and_candidate_registers_are_not_fabricated():
 p=artifact_paths(); assert all(x.exists() for x in p.values()); assert all(csv_rows(p[k])==() for k in ('geometry_changes','supersession_links','survey_observations','physical_state_changes')); assert len(csv_rows(p['qualification_results']))==1
