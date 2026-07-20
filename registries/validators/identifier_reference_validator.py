
"""
Nexa Provider Platform
File: registries/validators/identifier_reference_validator.py

Validates IdentifierReference objects against platform policy.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from registries.core.identifier_reference import IdentifierReference

from .validation_collector import RegistryValidationCollector
from .validation_message import RegistryValidationMessage, ValidationSeverity
from .validation_result import RegistryValidationResult

_VALUE_PATTERN = re.compile(r"^\S+$")


class IdentifierReferenceValidator:
    """Stateless validator for IdentifierReference."""

    @classmethod
    def validate(
        cls,
        reference: IdentifierReference,
        *,
        existing_reference_ids: Iterable[str] = (),
        existing_identifier_values: Iterable[str] = (),
    ) -> RegistryValidationResult:
        if not isinstance(reference, IdentifierReference):
            raise TypeError(
                "reference must be an IdentifierReference."
            )

        collector = RegistryValidationCollector()

        ids = {
            v.strip()
            for v in existing_reference_ids
            if isinstance(v, str) and v.strip()
        }
        values = {
            v.strip()
            for v in existing_identifier_values
            if isinstance(v, str) and v.strip()
        }

        if reference.reference_id in ids:
            collector.add(
                cls._msg(
                    ValidationSeverity.ERROR,
                    "REF-001",
                    "reference_id",
                    "Reference ID already exists.",
                    "Choose a globally unique reference ID.",
                )
            )

        if reference.identifier_value in values:
            collector.add(
                cls._msg(
                    ValidationSeverity.ERROR,
                    "REF-002",
                    "identifier_value",
                    "Identifier value already exists.",
                    "Use a unique identifier value where uniqueness is required.",
                )
            )

        if _VALUE_PATTERN.fullmatch(reference.identifier_value) is None:
            collector.add(
                cls._msg(
                    ValidationSeverity.ERROR,
                    "REF-003",
                    "identifier_value",
                    "Identifier value contains whitespace.",
                    "Remove whitespace from the identifier value.",
                )
            )

        if reference.active and not reference.sourced:
            collector.add(
                cls._msg(
                    ValidationSeverity.INFORMATION,
                    "REF-004",
                    "source_reference",
                    "Active identifier reference has no source reference.",
                    "Record the origin when available.",
                )
            )

        if len(reference.metadata) > 100:
            collector.add(
                cls._msg(
                    ValidationSeverity.WARNING,
                    "REF-005",
                    "metadata",
                    "Large metadata collection.",
                    "Reduce metadata or move extended data elsewhere.",
                )
            )

        return collector.build()

    @staticmethod
    def _msg(
        severity,
        code,
        field,
        message,
        suggestion,
    ):
        return RegistryValidationMessage(
            severity=severity,
            code=code,
            field=field,
            message=message,
            suggestion=suggestion,
        )


__all__ = (
    "IdentifierReferenceValidator",
)
