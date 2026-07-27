from types import MappingProxyType

import pytest

from registries.core import (
    BaseRegistry,
    RegistryDefinition,
    RegistryFamily,
    RegistryStatus,
)
from registries.governance import (
    RegistryLifecycle,
    RegistryLifecycleInputError,
    RegistryLifecycleTerminalStateError,
    RegistryLifecycleTransitionError,
)


def _registry(status=RegistryStatus.DRAFT, version=4):
    return BaseRegistry(
        RegistryDefinition(
            registry_id="npp.registry.citizens",
            registry_code="citizens",
            registry_name="Citizen Registry",
            family=RegistryFamily.CORE_INFRASTRUCTURE,
            status=status,
            description="Civil identity registry",
            version=version,
            metadata={"owner": "civil-registry", "classification": "restricted"},
        )
    )


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (RegistryStatus.DRAFT, RegistryStatus.ACTIVE),
        (RegistryStatus.DRAFT, RegistryStatus.RETIRED),
        (RegistryStatus.ACTIVE, RegistryStatus.SUSPENDED),
        (RegistryStatus.ACTIVE, RegistryStatus.RETIRED),
        (RegistryStatus.SUSPENDED, RegistryStatus.ACTIVE),
        (RegistryStatus.SUSPENDED, RegistryStatus.RETIRED),
    ],
)
def test_real_transitions_create_new_immutable_registry(current, target):
    original = _registry(current)
    result = RegistryLifecycle().transition(original, target)

    assert result.changed is True
    assert result.noop is False
    assert result.previous_status is current
    assert result.current_status is target
    assert result.registry is not original
    assert result.registry.definition is not original.definition
    assert result.registry.status is target
    assert result.registry.version == original.version + 1
    assert original.status is current
    assert original.version == 4


def test_transition_preserves_identity_and_unrelated_definition_fields():
    original = _registry()
    result = RegistryLifecycle().transition(original, " ACTIVE ")
    updated = result.registry

    assert updated.registry_id == original.registry_id
    assert updated.registry_code == original.registry_code
    assert updated.registry_name == original.registry_name
    assert updated.family is original.family
    assert updated.description == original.description
    assert dict(updated.metadata) == dict(original.metadata)
    assert isinstance(updated.metadata, MappingProxyType)
    assert updated.identity == original.identity


def test_noop_is_idempotent_and_does_not_increment_version():
    original = _registry(RegistryStatus.ACTIVE)
    result = RegistryLifecycle().transition(original, "active")
    assert result.changed is False
    assert result.registry is original
    assert result.registry.version == original.version
    assert result.metadata["version_changed"] is False


def test_invalid_and_terminal_transitions_are_rejected_without_mutation():
    draft = _registry(RegistryStatus.DRAFT)
    with pytest.raises(RegistryLifecycleTransitionError):
        RegistryLifecycle().transition(draft, RegistryStatus.SUSPENDED)
    assert draft.status is RegistryStatus.DRAFT
    assert draft.version == 4

    retired = _registry(RegistryStatus.RETIRED)
    with pytest.raises(RegistryLifecycleTerminalStateError):
        RegistryLifecycle().transition(retired, RegistryStatus.ACTIVE)
    assert retired.status is RegistryStatus.RETIRED


def test_lifecycle_helpers_delegate_to_policy():
    lifecycle = RegistryLifecycle()
    active = _registry(RegistryStatus.ACTIVE)
    assert lifecycle.is_operational(active)
    assert lifecycle.can_transition(active, "suspended")
    assert not lifecycle.can_transition(active, "draft")


def test_lifecycle_rejects_invalid_registry_and_policy_inputs():
    with pytest.raises(RegistryLifecycleInputError):
        RegistryLifecycle(policy=object())
    lifecycle = RegistryLifecycle()
    with pytest.raises(RegistryLifecycleInputError):
        lifecycle.transition(object(), RegistryStatus.ACTIVE)
    with pytest.raises(RegistryLifecycleInputError):
        lifecycle.is_operational(None)
