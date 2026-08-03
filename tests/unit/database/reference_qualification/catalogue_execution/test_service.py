import pytest
from database.reference_qualification.catalogue_execution import CataloguePlanExecutionRequest,CataloguePlanExecutionService,CataloguePlanPreviewService

class Executor:
    def execute(self,step,request,preview):
        from database.reference_qualification.catalogue_execution import CataloguePlanStepReceipt
        return CataloguePlanStepReceipt(step.step_id,step.file_id,step.target_kind,len(preview.selected_source_record_ids),len(preview.selected_source_record_ids),1,0,0,0,0,1,0,"passed",preview.selection_fingerprint)

def test_service_requires_exact_confirmation_and_aggregates_receipts():
    preview=CataloguePlanPreviewService("database/seeds")
    req=CataloguePlanExecutionRequest("multicultural-core","simulation",2,7,"operator:a","approver:b","rev")
    expected=preview.preview(req,database_name="npp_dev",environment="development")
    service=CataloguePlanExecutionService(preview,Executor())
    with pytest.raises(ValueError): service.run(req,database_name="npp_dev",environment="development",confirmation="wrong")
    receipt=service.run(req,database_name="npp_dev",environment="development",confirmation=expected.confirmation_token)
    assert receipt.status=="passed"
    assert receipt.imported_count==2
