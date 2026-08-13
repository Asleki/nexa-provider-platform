"""P006.7.1.3 sovereign operating-context contracts for NoveGeo.

Bundle 13B extends the locked Bundle 13A country identity through additive
reference contracts. It deliberately keeps realm, semantic runtime, record
effect scope, and approval state separate so simulation and production can
coexist without becoming interchangeable.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
import re

from shared.runtime.operation_runtime import OperationRuntimeMode

_REALM_ID = re.compile(r"^realm:[a-z0-9][a-z0-9:_-]{1,127}$")
_COUNTRY_ID = re.compile(r"^country:[a-z][a-z0-9_-]{1,63}$")


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")
    return " ".join(value.strip().split())


class RealmType(str, Enum):
    SIMULATED_SOVEREIGN_WORLD = "SIMULATED_SOVEREIGN_WORLD"


class ReferenceLifecycleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUPERSEDED = "SUPERSEDED"


class RecordEffectScope(str, Enum):
    SHARED_REFERENCE = "SHARED_REFERENCE"
    SIMULATION_ONLY = "SIMULATION_ONLY"
    PRODUCTION_ONLY = "PRODUCTION_ONLY"
    RUNTIME_SCOPED = "RUNTIME_SCOPED"
    HISTORICAL_REFERENCE = "HISTORICAL_REFERENCE"


class ApprovalState(str, Enum):
    DRAFT = "DRAFT"
    PROPOSED = "PROPOSED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    WITHDRAWN = "WITHDRAWN"
    SUPERSEDED = "SUPERSEDED"

    @property
    def terminal(self) -> bool:
        return self in {
            ApprovalState.APPROVED,
            ApprovalState.REJECTED,
            ApprovalState.WITHDRAWN,
            ApprovalState.SUPERSEDED,
        }


@dataclass(frozen=True, slots=True)
class WorldRealmReference:
    realm_id: str
    realm_code: str
    realm_name: str
    realm_type: RealmType | str
    country_id: str
    status: ReferenceLifecycleStatus | str
    effective_from: date

    def __post_init__(self) -> None:
        realm_id = _required_text(self.realm_id, "realm_id").lower()
        country_id = _required_text(self.country_id, "country_id").lower()
        if not _REALM_ID.fullmatch(realm_id):
            raise ValueError("realm_id must use the realm:<stable-key> namespace.")
        if not _COUNTRY_ID.fullmatch(country_id):
            raise ValueError("country_id must use the country:<stable-key> namespace.")
        realm_type = self.realm_type if isinstance(self.realm_type, RealmType) else RealmType(str(self.realm_type).upper())
        status = self.status if isinstance(self.status, ReferenceLifecycleStatus) else ReferenceLifecycleStatus(str(self.status).upper())
        if not isinstance(self.effective_from, date):
            raise TypeError("effective_from must be a date.")
        object.__setattr__(self, "realm_id", realm_id)
        object.__setattr__(self, "realm_code", _required_text(self.realm_code, "realm_code").upper())
        object.__setattr__(self, "realm_name", _required_text(self.realm_name, "realm_name"))
        object.__setattr__(self, "realm_type", realm_type)
        object.__setattr__(self, "country_id", country_id)
        object.__setattr__(self, "status", status)


@dataclass(frozen=True, slots=True)
class RuntimeReference:
    runtime_mode: OperationRuntimeMode | str
    canonical_label: str
    semantic_role: str
    status: ReferenceLifecycleStatus | str
    effective_from: date

    def __post_init__(self) -> None:
        runtime = self.runtime_mode if isinstance(self.runtime_mode, OperationRuntimeMode) else OperationRuntimeMode(str(self.runtime_mode).strip().lower())
        status = self.status if isinstance(self.status, ReferenceLifecycleStatus) else ReferenceLifecycleStatus(str(self.status).upper())
        if not isinstance(self.effective_from, date):
            raise TypeError("effective_from must be a date.")
        object.__setattr__(self, "runtime_mode", runtime)
        object.__setattr__(self, "canonical_label", _required_text(self.canonical_label, "canonical_label"))
        object.__setattr__(self, "semantic_role", _required_text(self.semantic_role, "semantic_role"))
        object.__setattr__(self, "status", status)


@dataclass(frozen=True, slots=True)
class AuthorityEffectReference:
    """Reference dimensions used by later authority/policy engines.

    This is not an authorization engine. It only preserves the governed
    distinction between runtime, effect scope, approval requirement and
    approval state.
    """

    runtime_mode: OperationRuntimeMode | str
    effect_scope: RecordEffectScope | str
    approval_required: bool
    approval_state: ApprovalState | str

    def __post_init__(self) -> None:
        runtime = self.runtime_mode if isinstance(self.runtime_mode, OperationRuntimeMode) else OperationRuntimeMode(str(self.runtime_mode).strip().lower())
        scope = self.effect_scope if isinstance(self.effect_scope, RecordEffectScope) else RecordEffectScope(str(self.effect_scope).upper())
        approval = self.approval_state if isinstance(self.approval_state, ApprovalState) else ApprovalState(str(self.approval_state).upper())
        if not isinstance(self.approval_required, bool):
            raise TypeError("approval_required must be boolean.")
        if scope is RecordEffectScope.SIMULATION_ONLY and runtime is OperationRuntimeMode.PRODUCTION:
            raise ValueError("SIMULATION_ONLY effect scope cannot be paired with production runtime.")
        if scope is RecordEffectScope.PRODUCTION_ONLY and runtime is OperationRuntimeMode.SIMULATION:
            raise ValueError("PRODUCTION_ONLY effect scope cannot be paired with simulation runtime.")
        object.__setattr__(self, "runtime_mode", runtime)
        object.__setattr__(self, "effect_scope", scope)
        object.__setattr__(self, "approval_state", approval)
