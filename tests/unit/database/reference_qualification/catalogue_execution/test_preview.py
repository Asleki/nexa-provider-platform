from database.reference_qualification.catalogue_execution import CataloguePlanExecutionRequest,CataloguePlanPreviewService

def test_preview_is_deterministic_and_bounded():
    service=CataloguePlanPreviewService("database/seeds")
    req=CataloguePlanExecutionRequest("native-core","simulation",3,99,repository_revision="rev")
    first=service.preview(req,database_name="npp_dev",environment="development")
    second=service.preview(req,database_name="npp_dev",environment="development")
    assert first.plan_fingerprint==second.plan_fingerprint
    assert len(first.steps)==3
    assert first.expected_candidate_count==9
    assert all(len(s.selected_source_record_ids)==3 for s in first.steps)
    assert first.confirmation_token.startswith("RUN CATALOGUE PLAN native-core npp_dev ")
