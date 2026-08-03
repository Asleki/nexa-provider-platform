from database.reference_qualification.catalogue_execution import CataloguePlanExecutionRequest,CataloguePlanPreviewService

def test_all_governed_plans_preview_against_real_manifests():
    service=CataloguePlanPreviewService("database/seeds")
    for plan in ("native-core","multicultural-core","multicultural-unicode"):
        result=service.preview(CataloguePlanExecutionRequest(plan,"simulation",2,17,repository_revision="test"),database_name="npp_dev",environment="development")
        assert result.expected_candidate_count==2*len(result.steps)
        assert all(step.source_row_count>=2 for step in result.steps)
