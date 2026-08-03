from database.reference_qualification.catalogue_execution import CataloguePlanExecutionRequest,CataloguePlanPreviewService,format_preview,format_payload

def test_preview_format_reports_zero_writes_and_json_is_machine_readable():
    p=CataloguePlanPreviewService("database/seeds").preview(CataloguePlanExecutionRequest("multicultural-unicode","simulation",1,2,repository_revision="rev"),database_name="npp_dev",environment="development")
    assert "Database writes performed: 0" in format_preview(p)
    assert '"plan_id": "multicultural-unicode"' in format_payload(p)
