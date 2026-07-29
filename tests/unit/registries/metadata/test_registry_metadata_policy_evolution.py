from tests.unit.registries.metadata.metadata_test_support import (
    make_classification,
    make_profile,
    make_training,
)


def test_privacy_can_tighten_without_changing_registry_identity():
    original = make_profile(profile_version=1)
    tightened = make_profile(
        profile_version=2,
        data_classification=make_classification(
            level="highly_restricted",
            contains_sensitive_personal_data=True,
        ),
        training_eligibility=make_training(
            status="prohibited",
            anonymisation_required=False,
            human_approval_required=False,
        ),
    )
    assert original.registry_id == tightened.registry_id
    assert original.data_classification.level.code == "restricted"
    assert tightened.data_classification.level.code == "highly_restricted"
    assert original.training_eligibility.status.value == "conditionally_eligible"
    assert tightened.training_eligibility.status.value == "prohibited"


def test_new_profile_does_not_mutate_old_profile():
    old = make_profile(profile_version=1, attributes={"policy": {"version": 1}})
    new = make_profile(profile_version=2, attributes={"policy": {"version": 2}})
    assert old.to_dict()["attributes"]["policy"]["version"] == 1
    assert new.to_dict()["attributes"]["policy"]["version"] == 2
