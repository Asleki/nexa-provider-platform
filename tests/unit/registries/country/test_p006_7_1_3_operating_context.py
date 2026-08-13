from datetime import date

import pytest

from shared.runtime.operation_runtime import OperationRuntimeMode
from registries.country.operating_context import (
    ApprovalState,
    AuthorityEffectReference,
    RecordEffectScope,
    RealmType,
    RuntimeReference,
    WorldRealmReference,
)


def test_p006_7_1_3_realm_and_semantic_runtime_remain_distinct_dimensions():
    realm = WorldRealmReference(
        realm_id="realm:nexilabs:novegeo",
        realm_code="NOVEGEO",
        realm_name="NoveGeo",
        realm_type="SIMULATED_SOVEREIGN_WORLD",
        country_id="country:novegeo",
        status="ACTIVE",
        effective_from=date(2026, 8, 12),
    )
    runtime = RuntimeReference(
        runtime_mode="simulation",
        canonical_label="Simulation",
        semantic_role="simulated_world_operations",
        status="ACTIVE",
        effective_from=date(2026, 8, 12),
    )
    assert realm.realm_type is RealmType.SIMULATED_SOVEREIGN_WORLD
    assert realm.country_id == "country:novegeo"
    assert runtime.runtime_mode is OperationRuntimeMode.SIMULATION
    assert not hasattr(realm, "runtime_mode")


def test_p006_7_1_3_effect_scope_and_approval_are_not_runtime_aliases():
    reference = AuthorityEffectReference(
        runtime_mode="simulation",
        effect_scope="RUNTIME_SCOPED",
        approval_required=True,
        approval_state="UNDER_REVIEW",
    )
    assert reference.runtime_mode is OperationRuntimeMode.SIMULATION
    assert reference.effect_scope is RecordEffectScope.RUNTIME_SCOPED
    assert reference.approval_state is ApprovalState.UNDER_REVIEW
    assert reference.approval_state.terminal is False
    assert ApprovalState.APPROVED.terminal is True


def test_p006_7_1_3_runtime_specific_effects_cannot_cross_runtime_boundary():
    with pytest.raises(ValueError, match="SIMULATION_ONLY"):
        AuthorityEffectReference("production", "SIMULATION_ONLY", True, "APPROVED")
    with pytest.raises(ValueError, match="PRODUCTION_ONLY"):
        AuthorityEffectReference("simulation", "PRODUCTION_ONLY", True, "APPROVED")


def test_p006_7_1_3_governed_vocabularies_are_complete():
    assert {scope.value for scope in RecordEffectScope} == {
        "SHARED_REFERENCE",
        "SIMULATION_ONLY",
        "PRODUCTION_ONLY",
        "RUNTIME_SCOPED",
        "HISTORICAL_REFERENCE",
    }
    assert {state.value for state in ApprovalState} == {
        "DRAFT",
        "PROPOSED",
        "UNDER_REVIEW",
        "APPROVED",
        "REJECTED",
        "WITHDRAWN",
        "SUPERSEDED",
    }
