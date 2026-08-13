"""P006.7.2.2 NNGLA registry-domain catalogue."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from shared.runtime.operation_runtime import OperationRuntimeMode
from registries.country.operating_context import RecordEffectScope

class NNGLARecordFamily(str, Enum):
    GEOGRAPHIC_NAME = "GEOGRAPHIC_NAME"
    GEOGRAPHIC_FEATURE = "GEOGRAPHIC_FEATURE"
    GEOMETRY = "GEOMETRY"
    ADMIN_AREA = "ADMIN_AREA"
    ROAD_REFERENCE = "ROAD_REFERENCE"
    ADDRESS_REFERENCE = "ADDRESS_REFERENCE"
    PARCEL = "PARCEL"
    TITLE = "TITLE"
    STATE_LAND = "STATE_LAND"

@dataclass(frozen=True, slots=True)
class DomainRuntimeRule:
    record_family: NNGLARecordFamily
    runtime_mode: OperationRuntimeMode
    permission_code: str
    effect_scope: RecordEffectScope
    approval_required: bool
    status: str = "ACTIVE"

    def __post_init__(self) -> None:
        if not self.permission_code.strip():
            raise ValueError("permission_code is required")
        if self.effect_scope is RecordEffectScope.SIMULATION_ONLY and self.runtime_mode is OperationRuntimeMode.PRODUCTION:
            raise ValueError("simulation-only effect cannot be production runtime")
        if self.effect_scope is RecordEffectScope.PRODUCTION_ONLY and self.runtime_mode is OperationRuntimeMode.SIMULATION:
            raise ValueError("production-only effect cannot be simulation runtime")

class NNGLADomainCatalogue:
    def __init__(self, rules: tuple[DomainRuntimeRule, ...]):
        keys = [(r.record_family, r.runtime_mode) for r in rules]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate record-family/runtime rule")
        self._rules = tuple(rules)

    @property
    def families(self) -> frozenset[NNGLARecordFamily]:
        return frozenset(r.record_family for r in self._rules)

    def rule_for(self, family: NNGLARecordFamily, runtime: OperationRuntimeMode) -> DomainRuntimeRule:
        for rule in self._rules:
            if rule.record_family is family and rule.runtime_mode is runtime:
                return rule
        raise KeyError((family, runtime))
