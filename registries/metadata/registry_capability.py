"""Immutable declaration of one capability supported by a registry."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from .registry_capability_category import RegistryCapabilityCategory
from .registry_metadata_errors import RegistryCapabilityError

@dataclass(frozen=True, slots=True)
class RegistryCapability:
    capability_id: str
    capability_code: str
    capability_name: str
    category: RegistryCapabilityCategory
    description: str = ""
    supported: bool = True
    simulation_supported: bool = True
    production_supported: bool = False
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        for name in ("capability_id", "capability_code", "capability_name"):
            value = getattr(self, name)
            if not isinstance(value, str): raise TypeError(f"{name} must be text.")
            value = value.strip()
            if not value: raise RegistryCapabilityError(f"{name} cannot be empty.")
            if name == "capability_code": value = value.upper()
            object.__setattr__(self, name, value)
        if not isinstance(self.description, str): raise TypeError("description must be text.")
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "category", RegistryCapabilityCategory.from_value(self.category))
        for name in ("supported", "simulation_supported", "production_supported"):
            if not isinstance(getattr(self, name), bool): raise TypeError(f"{name} must be a boolean.")
        if self.production_supported and not self.supported:
            raise RegistryCapabilityError("production_supported requires supported=True.")
        if self.simulation_supported and not self.supported:
            raise RegistryCapabilityError("simulation_supported requires supported=True.")
        if isinstance(self.version, bool) or not isinstance(self.version, int): raise TypeError("version must be an integer.")
        if self.version < 1: raise RegistryCapabilityError("version must be at least 1.")
        if not isinstance(self.attributes, Mapping): raise TypeError("attributes must be a mapping.")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def to_dict(self):
        return {"capability_id": self.capability_id, "capability_code": self.capability_code,
                "capability_name": self.capability_name, "category": self.category.value,
                "description": self.description, "supported": self.supported,
                "simulation_supported": self.simulation_supported,
                "production_supported": self.production_supported, "version": self.version,
                "attributes": dict(self.attributes)}

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, Mapping): raise TypeError("data must be a mapping.")
        return cls(**dict(data))

__all__ = ["RegistryCapability"]
