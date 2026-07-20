"""
Nexa Provider Platform
Registry Foundation Public API

Exports the public immutable Registry Foundation models.
"""

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
    "NumberingMode",
    "NumberingStrategy",
    "NumberingStrategyError",
    "DEFAULT_IDENTIFIER_REFERENCE_VERSION",
    "IdentifierReference",
    "IdentifierReferenceError",
)
