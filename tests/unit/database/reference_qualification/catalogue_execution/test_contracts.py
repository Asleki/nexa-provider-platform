import pytest
from database.reference_qualification.catalogue_execution import CataloguePlanExecutionRequest

def test_request_requires_explicit_valid_runtime_and_distinct_actors():
    request=CataloguePlanExecutionRequest("native-core","production",5,42,"operator:a","approver:b","abc")
    assert request.sample_size==5
    with pytest.raises(ValueError): CataloguePlanExecutionRequest("native-core","live",5,42)
    with pytest.raises(ValueError): CataloguePlanExecutionRequest("native-core","production",5,42,"same","same")
