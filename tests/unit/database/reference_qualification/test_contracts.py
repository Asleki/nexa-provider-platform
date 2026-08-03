import pytest

from database.reference_qualification.contracts import (
    ProductionNameQualificationRequest,
    QualificationFinding,
    SchemaColumn,
)


def test_contracts_validate_required_fields_and_actor_separation():
    request = ProductionNameQualificationRequest(
        raw_name_value="  Mary   Jane  ",
        requested_name_kind="first_name",
        sex_usage="female",
        submitter_actor_id="operator:1",
        approver_actor_id="approver:1",
        qualification_id="qualification:1",
    )
    assert request.raw_name_value == "Mary   Jane"
    assert QualificationFinding("NORMALIZED", "passed", "ok").status == "passed"
    assert SchemaColumn("reference", "canonical_name", "name_id", "text", False).ordinal_position == 1

    with pytest.raises(ValueError, match="different actors"):
        ProductionNameQualificationRequest(
            raw_name_value="Mary",
            requested_name_kind="first_name",
            sex_usage="female",
            submitter_actor_id="operator:1",
            approver_actor_id="operator:1",
            qualification_id="qualification:2",
        )
