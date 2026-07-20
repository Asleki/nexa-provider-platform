
"""
Nexa Provider Platform
File: registries/validators/namespace_validator.py

Validates NamespaceDefinition objects against namespace policy.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from registries.core.namespace_definition import NamespaceDefinition

from .validation_collector import RegistryValidationCollector
from .validation_message import RegistryValidationMessage, ValidationSeverity
from .validation_result import RegistryValidationResult

_NAMESPACE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_NAMESPACE_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


class NamespaceValidator:
    """Stateless validator for NamespaceDefinition."""

    @classmethod
    def validate(
        cls,
        definition: NamespaceDefinition,
        *,
        existing_namespace_ids: Iterable[str] = (),
        existing_namespace_codes: Iterable[str] = (),
    ) -> RegistryValidationResult:
        if not isinstance(definition, NamespaceDefinition):
            raise TypeError("definition must be a NamespaceDefinition.")

        c = RegistryValidationCollector()

        ids = {i.strip() for i in existing_namespace_ids if isinstance(i, str) and i.strip()}
        codes = {i.strip().casefold() for i in existing_namespace_codes if isinstance(i, str) and i.strip()}

        if _NAMESPACE_ID_PATTERN.fullmatch(definition.namespace_id) is None:
            c.add(cls._msg("ERROR","NS-001","namespace_id","Namespace ID contains unsupported characters.","Use only letters, digits, ., _, :, -."))
        if definition.namespace_id in ids:
            c.add(cls._msg("ERROR","NS-002","namespace_id","Namespace ID already exists.","Choose a unique namespace ID."))

        if _NAMESPACE_CODE_PATTERN.fullmatch(definition.namespace_code) is None:
            c.add(cls._msg("ERROR","NS-003","namespace_code","Namespace code must be uppercase letters, digits and underscores.","Use canonical uppercase code."))
        if definition.namespace_code.casefold() in codes:
            c.add(cls._msg("ERROR","NS-004","namespace_code","Namespace code already exists.","Choose a unique namespace code."))

        if definition.namespace_name.upper() == definition.namespace_code:
            c.add(cls._msg("WARNING","NS-005","namespace_name","Namespace name matches namespace code.","Use a more descriptive name."))

        if definition.active and not definition.description:
            c.add(cls._msg("INFORMATION","NS-006","description","Active namespace has no description.","Add a description."))

        if len(definition.metadata) > 100:
            c.add(cls._msg("WARNING","NS-007","metadata","Large metadata collection.","Reduce metadata or move extended data elsewhere."))

        return c.build()

    @staticmethod
    def _msg(level, code, field, message, suggestion):
        sev = {
            "ERROR": ValidationSeverity.ERROR,
            "WARNING": ValidationSeverity.WARNING,
            "INFORMATION": ValidationSeverity.INFORMATION,
        }[level]
        return RegistryValidationMessage(
            severity=sev,
            code=code,
            field=field,
            message=message,
            suggestion=suggestion,
        )


__all__ = ["NamespaceValidator"]
