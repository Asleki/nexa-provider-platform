"""P006.7.3 governed geographic-name catalogue contracts."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from registries.country.operating_context import RecordEffectScope

class GeographicNameRole(str, Enum):
    PRIMARY = "PRIMARY"
    ALTERNATE = "ALTERNATE"
    HISTORIC = "HISTORIC"
    NICKNAME = "NICKNAME"

@dataclass(frozen=True, slots=True)
class NamingStatusDefinition:
    naming_status_code: str
    canonical_label: str
    can_display_publicly: bool
    can_be_primary_name: bool
    requires_approval: bool
    requires_gazette: bool
    terminal_status: bool
    description: str

@dataclass(frozen=True, slots=True)
class GazetteActionDefinition:
    gazette_action_code: str
    canonical_label: str
    subject_family: str
    creates_legal_effect: bool
    requires_previous_record: bool
    reversible: bool
    status: str
    description: str

@dataclass(frozen=True, slots=True)
class GeographicName:
    name_id: str
    canonical_name: str
    ascii_name: str
    name_family: str
    naming_status_code: str
    runtime_effect_scope: RecordEffectScope
    source_dataset_id: str
    source_basis: str
    record_status: str
    nickname: str | None = None

    def __post_init__(self) -> None:
        if not self.name_id.startswith("NG-NAM-"):
            raise ValueError("name_id must use NG-NAM namespace")
        if not self.canonical_name.strip() or not self.ascii_name.strip():
            raise ValueError("canonical/ascii names are required")
        if not isinstance(self.runtime_effect_scope, RecordEffectScope):
            object.__setattr__(self, "runtime_effect_scope", RecordEffectScope(str(self.runtime_effect_scope)))
        if self.runtime_effect_scope is not RecordEffectScope.SHARED_REFERENCE:
            raise ValueError("governed geographic-name identities are shared references")

class MemoryGeographicNameRepository:
    def __init__(self) -> None:
        self._items: dict[str, GeographicName] = {}

    def add(self, record: GeographicName) -> GeographicName:
        prior = self._items.get(record.name_id)
        if prior is not None and prior != record:
            raise ValueError("geographic-name identifier collision")
        self._items[record.name_id] = record
        return record

    def get(self, name_id: str) -> GeographicName | None:
        return self._items.get(name_id)

    def all(self) -> tuple[GeographicName, ...]:
        return tuple(self._items[k] for k in sorted(self._items))

__all__ = ["GeographicNameRole", "NamingStatusDefinition", "GazetteActionDefinition", "GeographicName", "MemoryGeographicNameRepository"]
