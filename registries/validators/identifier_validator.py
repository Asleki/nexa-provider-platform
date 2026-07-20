
"""
Nexa Provider Platform
File: registries/validators/identifier_validator.py

Validates IdentifierDefinition objects against platform policy.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from registries.core.identifier_definition import IdentifierDefinition

from .validation_collector import RegistryValidationCollector
from .validation_message import RegistryValidationMessage, ValidationSeverity
from .validation_result import RegistryValidationResult

_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")


class IdentifierValidator:
    """Stateless validator for IdentifierDefinition."""

    @classmethod
    def validate(
        cls,
        definition: IdentifierDefinition,
        *,
        existing_identifier_ids: Iterable[str] = (),
        existing_identifier_codes: Iterable[str] = (),
    ) -> RegistryValidationResult:
        if not isinstance(definition, IdentifierDefinition):
            raise TypeError("definition must be an IdentifierDefinition.")

        c = RegistryValidationCollector()

        ids = {v.strip() for v in existing_identifier_ids if isinstance(v, str) and v.strip()}
        codes = {v.strip().casefold() for v in existing_identifier_codes if isinstance(v, str) and v.strip()}

        if _ID_PATTERN.fullmatch(definition.identifier_id) is None:
            c.add(cls._m(ValidationSeverity.ERROR,"REG-ID-001","identifier_id","Unsupported identifier ID format.","Use letters, digits, ., _, :, -."))
        if definition.identifier_id in ids:
            c.add(cls._m(ValidationSeverity.ERROR,"REG-ID-002","identifier_id","Identifier ID already exists.","Choose a unique identifier ID."))

        if _CODE_PATTERN.fullmatch(definition.identifier_code) is None:
            c.add(cls._m(ValidationSeverity.ERROR,"REG-ID-003","identifier_code","Identifier code is not canonical.","Use uppercase letters, digits and underscores."))
        if definition.identifier_code.casefold() in codes:
            c.add(cls._m(ValidationSeverity.ERROR,"REG-ID-004","identifier_code","Identifier code already exists.","Choose a unique identifier code."))

        if definition.has_pattern:
            try:
                re.compile(definition.pattern or "")
            except re.error:
                c.add(cls._m(ValidationSeverity.ERROR,"REG-ID-005","pattern","Pattern is not a valid regular expression.","Correct the regular expression."))

        if definition.has_prefix and definition.pattern:
            if not definition.case_sensitive and (definition.prefix or "").lower() != (definition.prefix or ""):
                c.add(cls._m(ValidationSeverity.INFORMATION,"REG-ID-006","prefix","Mixed-case prefix with case-insensitive identifiers.","Consider using a single-case prefix."))

        if definition.active and not definition.description:
            c.add(cls._m(ValidationSeverity.INFORMATION,"REG-ID-007","description","Active identifier has no description.","Add a description."))

        if len(definition.metadata) > 100:
            c.add(cls._m(ValidationSeverity.WARNING,"REG-ID-008","metadata","Large metadata collection.","Reduce metadata or externalize extended data."))

        return c.build()

    @staticmethod
    def _m(severity, code, field, message, suggestion):
        return RegistryValidationMessage(
            severity=severity,
            code=code,
            field=field,
            message=message,
            suggestion=suggestion,
        )


__all__ = ["IdentifierValidator"]
