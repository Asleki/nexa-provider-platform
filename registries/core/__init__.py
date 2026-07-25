"""
Nexa Provider Platform
Registry Foundation Public API

Exports the public immutable Registry Foundation models.
"""


from .registry_family import RegistryFamily
from .registry_status import RegistryStatus
from .identifier_lifecycle import IdentifierLifecycle

from .registry_definition import (
    DEFAULT_REGISTRY_DEFINITION_VERSION,
    RegistryDefinition,
    RegistryDefinitionError,
)

from .namespace_definition import (
    DEFAULT_NAMESPACE_DEFINITION_VERSION,
    NamespaceDefinition,
    NamespaceDefinitionError,
)

from .identifier_definition import (
    DEFAULT_IDENTIFIER_CASE_SENSITIVE,
    DEFAULT_IDENTIFIER_DEFINITION_VERSION,
    IdentifierDefinition,
    IdentifierDefinitionError,
)

from .numbering_strategy import (
    DEFAULT_NUMBERING_STRATEGY_VERSION,
    NumberingMode,
    NumberingStrategy,
    NumberingStrategyError,
)

from .identifier_reference import (
    DEFAULT_IDENTIFIER_REFERENCE_VERSION,
    IdentifierReference,
    IdentifierReferenceError,
)

__all__ = (
    "RegistryFamily",
    "RegistryStatus",
    "IdentifierLifecycle",
    "DEFAULT_REGISTRY_DEFINITION_VERSION",
    "RegistryDefinition",
    "RegistryDefinitionError",
    "DEFAULT_NAMESPACE_DEFINITION_VERSION",
    "NamespaceDefinition",
    "NamespaceDefinitionError",
    "DEFAULT_IDENTIFIER_CASE_SENSITIVE",
    "DEFAULT_IDENTIFIER_DEFINITION_VERSION",
    "IdentifierDefinition",
    "IdentifierDefinitionError",
    "DEFAULT_NUMBERING_STRATEGY_VERSION",
    "NumberingMode",
    "NumberingStrategy",
    "NumberingStrategyError",
    "DEFAULT_IDENTIFIER_REFERENCE_VERSION",
    "IdentifierReference",
    "IdentifierReferenceError",
)
