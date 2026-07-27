import pytest

from registries.core import RegistryStatus
from registries.governance import (
    RegistryLifecycleInputError,
    RegistryLifecyclePolicy,
    RegistryLifecycleTerminalStateError,
    RegistryLifecycleTransitionError,
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
def test_approved_transition_matrix(current, target):
    assert RegistryLifecyclePolicy.can_transition(current, target)
    assert RegistryLifecyclePolicy.require_transition(current, target) == (
        current,
        target,
    )


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (RegistryStatus.DRAFT, RegistryStatus.SUSPENDED),
        (RegistryStatus.ACTIVE, RegistryStatus.DRAFT),
        (RegistryStatus.SUSPENDED, RegistryStatus.DRAFT),
    ],
)
def test_disallowed_non_terminal_transitions(current, target):
    assert not RegistryLifecyclePolicy.can_transition(current, target)
    with pytest.raises(RegistryLifecycleTransitionError) as captured:
        RegistryLifecyclePolicy.require_transition(current, target)
    assert captured.value.current_status == current.value
    assert captured.value.target_status == target.value


@pytest.mark.parametrize(
    "target",
    [RegistryStatus.DRAFT, RegistryStatus.ACTIVE, RegistryStatus.SUSPENDED],
)
def test_retired_is_terminal(target):
    assert not RegistryLifecyclePolicy.can_transition(
        RegistryStatus.RETIRED,
        target,
    )
    with pytest.raises(RegistryLifecycleTerminalStateError):
        RegistryLifecyclePolicy.require_transition(
            RegistryStatus.RETIRED,
            target,
        )


def test_noop_is_idempotent_by_default_and_can_be_rejected_explicitly():
    assert RegistryLifecyclePolicy.can_transition(" ACTIVE ", "active")
    assert RegistryLifecyclePolicy.require_transition(" ACTIVE ", "active") == (
        RegistryStatus.ACTIVE,
        RegistryStatus.ACTIVE,
    )
    assert not RegistryLifecyclePolicy.can_transition(
        RegistryStatus.ACTIVE,
        RegistryStatus.ACTIVE,
        allow_noop=False,
    )
    with pytest.raises(RegistryLifecycleTransitionError):
        RegistryLifecyclePolicy.require_transition(
            RegistryStatus.ACTIVE,
            RegistryStatus.ACTIVE,
            allow_noop=False,
        )


def test_status_helpers_and_allowed_targets_are_deterministic():
    assert RegistryLifecyclePolicy.is_operational(" active ")
    assert not RegistryLifecyclePolicy.is_operational("suspended")
    assert RegistryLifecyclePolicy.is_terminal("RETIRED")
    assert RegistryLifecyclePolicy.allowed_targets("draft") == (
        RegistryStatus.ACTIVE,
        RegistryStatus.RETIRED,
    )


@pytest.mark.parametrize("value", [None, object(), "", "unknown"])
def test_invalid_status_inputs_are_controlled(value):
    with pytest.raises(RegistryLifecycleInputError):
        RegistryLifecyclePolicy.normalize_status(value)


def test_allow_noop_must_be_boolean():
    with pytest.raises(RegistryLifecycleInputError):
        RegistryLifecyclePolicy.can_transition(
            RegistryStatus.ACTIVE,
            RegistryStatus.ACTIVE,
            allow_noop=1,
        )
