from tests.unit.registries.metadata.metadata_test_support import make_capability, make_profile


def test_multiple_identifiers_coexist_without_becoming_registry_identity():
    profile = make_profile(
        registry_id="manufacturer.employee.registry",
        attributes={
            "country_registry_id": "country.ke",
            "jurisdiction_policy_id": "employment.ke.v1",
            "form_schema_id": "employee.ke.v1",
            "source_document_registry_id": "identity.document.ke",
        },
    )
    assert profile.registry_id == "manufacturer.employee.registry"
    assert profile.to_dict()["attributes"] == {
        "country_registry_id": "country.ke",
        "jurisdiction_policy_id": "employment.ke.v1",
        "form_schema_id": "employee.ke.v1",
        "source_document_registry_id": "identity.document.ke",
    }


def test_similar_human_readable_names_do_not_make_distinct_capabilities_duplicates():
    first = make_capability(
        capability_id="employee-one",
        capability_code="EMPLOYEE.ONE",
        capability_name="Alex Malunda",
    )
    second = make_capability(
        capability_id="employee-two",
        capability_code="EMPLOYEE.TWO",
        capability_name="Alex Malunda",
    )
    profile = make_profile(capabilities=(first, second))
    assert [item.capability_code for item in profile.capabilities] == [
        "EMPLOYEE.ONE",
        "EMPLOYEE.TWO",
    ]


def test_profile_version_changes_without_replacing_registry_identity():
    first = make_profile(profile_version=1)
    second = make_profile(profile_version=2)
    assert first.registry_id == second.registry_id
    assert first.profile_version != second.profile_version
