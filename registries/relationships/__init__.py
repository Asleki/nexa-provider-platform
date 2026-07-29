"""Public contracts for the Cross-Registry Relationship Foundation."""

from .registry_reference import RegistryReference, RegistryReferenceError
from .relationship_definition import (
    RelationshipDefinition,
    RelationshipDefinitionError,
)
from .relationship_type import RelationshipType, RelationshipTypeError

__all__ = [
    "RegistryReference",
    "RegistryReferenceError",
    "RelationshipDefinition",
    "RelationshipDefinitionError",
    "RelationshipType",
    "RelationshipTypeError",
]
