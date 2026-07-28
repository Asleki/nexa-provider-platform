import pytest

from registries.metadata import RegistryCapability, RegistryCapabilityError


def _capability(**overrides):
    values = {
        "capability_id": "education-school-register-v1",
        "capability_code": "EDUCATION.SCHOOL.REGISTER",
        "capability_name": "Register School",
        "category": "identity",
    }
    values.update(overrides)
    return RegistryCapability(**values)


def test_hierarchical_code_is_normalized_and_future_domain_neutral():
    capability = _capability(capability_code=" education.school.register ")
    assert capability.capability_code == "EDUCATION.SCHOOL.REGISTER"


@pytest.mark.parametrize(
    "code",
    ["REGISTER", ".EDUCATION.REGISTER", "EDUCATION..REGISTER", "EDUCATION.REGISTER-ITEM"],
)
def test_invalid_capability_codes_are_rejected(code):
    with pytest.raises(RegistryCapabilityError):
        _capability(capability_code=code)


@pytest.mark.parametrize("capability_id", [" bad id ", "@bad", "-leading"])
def test_invalid_capability_identifiers_are_rejected(capability_id):
    with pytest.raises(RegistryCapabilityError):
        _capability(capability_id=capability_id)


def test_unknown_category_is_reported_as_capability_error():
    with pytest.raises(RegistryCapabilityError):
        _capability(category="unknown")


@pytest.mark.parametrize("field", ["supported", "simulation_supported", "production_supported"])
def test_runtime_support_flags_require_real_booleans(field):
    with pytest.raises(TypeError):
        _capability(**{field: 1})


def test_unsupported_capability_may_disable_both_runtime_routes():
    capability = _capability(
        supported=False,
        simulation_supported=False,
        production_supported=False,
    )
    assert capability.supported is False
