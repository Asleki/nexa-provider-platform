"""
============================================================
Nexa Provider Platform
File: registries/validators/registry_validator.py
Layer: Registry Validation Foundation
Milestone: NPP-M006.2 — Registry Foundation
============================================================

Purpose
-------
Validates immutable RegistryDefinition objects against Registry
Foundation policy that is intentionally broader than the model's
construction-time invariants.

The validator performs local definition checks and optional
catalogue-aware uniqueness checks without depending on storage,
repositories, logging, runtime state, or external services.

Validation remains non-mutating. Every finding is returned through
RegistryValidationResult.
============================================================
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Final

from registries.core.registry_definition import RegistryDefinition

from .validation_collector import RegistryValidationCollector
from .validation_message import (
    RegistryValidationMessage,
    ValidationSeverity,
)
from .validation_result import RegistryValidationResult


MINIMUM_REGISTRY_CODE_LENGTH: Final[int] = 2
MAXIMUM_REGISTRY_CODE_LENGTH: Final[int] = 64
MAXIMUM_REGISTRY_ID_LENGTH: Final[int] = 200
MAXIMUM_REGISTRY_NAME_LENGTH: Final[int] = 200
MAXIMUM_REGISTRY_DESCRIPTION_LENGTH: Final[int] = 2_000
MAXIMUM_REGISTRY_METADATA_ENTRIES: Final[int] = 100
MAXIMUM_REGISTRY_METADATA_KEY_LENGTH: Final[int] = 200

_REGISTRY_ID_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:-]*$"
)
_REGISTRY_CODE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"^[A-Z][A-Z0-9_]*$"
)


class RegistryValidator:
    """
    Stateless validator for RegistryDefinition objects.

    Optional existing identifier and code collections allow the
    caller to perform catalogue-aware duplicate checks while
    keeping this module independent from any repository.
    """

    __slots__ = ()

    @classmethod
    def validate(
        cls,
        definition: RegistryDefinition,
        *,
        existing_registry_ids: Iterable[str] = (),
        existing_registry_codes: Iterable[str] = (),
        reserved_registry_codes: Iterable[str] = (),
    ) -> RegistryValidationResult:
        """
        Validate one registry definition.

        Parameters
        ----------
        definition:
            RegistryDefinition to validate.

        existing_registry_ids:
            Registry IDs already owned by other definitions.

        existing_registry_codes:
            Registry codes already owned by other definitions.

        reserved_registry_codes:
            Codes that platform policy forbids for new registry
            definitions.
        """

        if not isinstance(definition, RegistryDefinition):
            raise TypeError(
                "definition must be a RegistryDefinition."
            )

        collector = RegistryValidationCollector()

        cls._validate_registry_id(
            definition,
            collector,
            existing_registry_ids=existing_registry_ids,
        )
        cls._validate_registry_code(
            definition,
            collector,
            existing_registry_codes=existing_registry_codes,
            reserved_registry_codes=reserved_registry_codes,
        )
        cls._validate_registry_name(
            definition,
            collector,
        )
        cls._validate_description(
            definition,
            collector,
        )
        cls._validate_version(
            definition,
            collector,
        )
        cls._validate_metadata(
            definition,
            collector,
        )

        return collector.build()

    @classmethod
    def _validate_registry_id(
        cls,
        definition: RegistryDefinition,
        collector: RegistryValidationCollector,
        *,
        existing_registry_ids: Iterable[str],
    ) -> None:
        registry_id = definition.registry_id

        if len(registry_id) > MAXIMUM_REGISTRY_ID_LENGTH:
            collector.add(
                cls._error(
                    code="REG-DEF-001",
                    field="registry_id",
                    message=(
                        "Registry ID exceeds the maximum supported "
                        f"length of {MAXIMUM_REGISTRY_ID_LENGTH} characters."
                    ),
                    suggestion=(
                        "Use a shorter stable registry identifier."
                    ),
                )
            )

        if _REGISTRY_ID_PATTERN.fullmatch(registry_id) is None:
            collector.add(
                cls._error(
                    code="REG-DEF-002",
                    field="registry_id",
                    message=(
                        "Registry ID contains unsupported characters."
                    ),
                    suggestion=(
                        "Use letters, numbers, periods, underscores, "
                        "colons, or hyphens, beginning with a letter "
                        "or number."
                    ),
                )
            )

        normalized_existing_ids = cls._normalize_comparison_values(
            existing_registry_ids,
            field_name="existing_registry_ids",
            case_sensitive=True,
        )

        if registry_id in normalized_existing_ids:
            collector.add(
                cls._error(
                    code="REG-DEF-003",
                    field="registry_id",
                    message=(
                        "Registry ID is already assigned to another "
                        "registry definition."
                    ),
                    suggestion=(
                        "Choose a globally unique registry ID."
                    ),
                )
            )

    @classmethod
    def _validate_registry_code(
        cls,
        definition: RegistryDefinition,
        collector: RegistryValidationCollector,
        *,
        existing_registry_codes: Iterable[str],
        reserved_registry_codes: Iterable[str],
    ) -> None:
        registry_code = definition.registry_code

        if len(registry_code) < MINIMUM_REGISTRY_CODE_LENGTH:
            collector.add(
                cls._error(
                    code="REG-DEF-004",
                    field="registry_code",
                    message=(
                        "Registry code is shorter than the minimum "
                        f"supported length of {MINIMUM_REGISTRY_CODE_LENGTH}."
                    ),
                    suggestion=(
                        "Use a concise code containing at least two "
                        "characters."
                    ),
                )
            )

        if len(registry_code) > MAXIMUM_REGISTRY_CODE_LENGTH:
            collector.add(
                cls._error(
                    code="REG-DEF-005",
                    field="registry_code",
                    message=(
                        "Registry code exceeds the maximum supported "
                        f"length of {MAXIMUM_REGISTRY_CODE_LENGTH}."
                    ),
                    suggestion="Use a shorter canonical registry code.",
                )
            )

        if _REGISTRY_CODE_PATTERN.fullmatch(registry_code) is None:
            collector.add(
                cls._error(
                    code="REG-DEF-006",
                    field="registry_code",
                    message=(
                        "Registry code does not follow the canonical "
                        "uppercase code format."
                    ),
                    suggestion=(
                        "Begin with an uppercase letter and use only "
                        "uppercase letters, numbers, and underscores."
                    ),
                )
            )

        normalized_existing_codes = cls._normalize_comparison_values(
            existing_registry_codes,
            field_name="existing_registry_codes",
            case_sensitive=False,
        )

        if registry_code.casefold() in normalized_existing_codes:
            collector.add(
                cls._error(
                    code="REG-DEF-007",
                    field="registry_code",
                    message=(
                        "Registry code is already assigned to another "
                        "registry definition."
                    ),
                    suggestion=(
                        "Choose a registry code that is unique "
                        "regardless of letter case."
                    ),
                )
            )

        normalized_reserved_codes = cls._normalize_comparison_values(
            reserved_registry_codes,
            field_name="reserved_registry_codes",
            case_sensitive=False,
        )

        if registry_code.casefold() in normalized_reserved_codes:
            collector.add(
                cls._error(
                    code="REG-DEF-008",
                    field="registry_code",
                    message=(
                        "Registry code is reserved by platform policy."
                    ),
                    suggestion=(
                        "Choose a non-reserved canonical registry code."
                    ),
                )
            )

    @classmethod
    def _validate_registry_name(
        cls,
        definition: RegistryDefinition,
        collector: RegistryValidationCollector,
    ) -> None:
        registry_name = definition.registry_name

        if len(registry_name) > MAXIMUM_REGISTRY_NAME_LENGTH:
            collector.add(
                cls._error(
                    code="REG-DEF-009",
                    field="registry_name",
                    message=(
                        "Registry name exceeds the maximum supported "
                        f"length of {MAXIMUM_REGISTRY_NAME_LENGTH} "
                        "characters."
                    ),
                    suggestion=(
                        "Use a shorter human-readable registry name."
                    ),
                )
            )

        if registry_name.upper() == definition.registry_code:
            collector.add(
                cls._warning(
                    code="REG-DEF-010",
                    field="registry_name",
                    message=(
                        "Registry name is identical to the canonical "
                        "registry code."
                    ),
                    suggestion=(
                        "Provide a clearer human-readable name when "
                        "the code alone is not descriptive."
                    ),
                )
            )

    @classmethod
    def _validate_description(
        cls,
        definition: RegistryDefinition,
        collector: RegistryValidationCollector,
    ) -> None:
        description = definition.description

        if len(description) > MAXIMUM_REGISTRY_DESCRIPTION_LENGTH:
            collector.add(
                cls._error(
                    code="REG-DEF-011",
                    field="description",
                    message=(
                        "Registry description exceeds the maximum "
                        f"supported length of "
                        f"{MAXIMUM_REGISTRY_DESCRIPTION_LENGTH} characters."
                    ),
                    suggestion=(
                        "Shorten the description or move extended "
                        "documentation outside the definition."
                    ),
                )
            )

        if definition.active and not description:
            collector.add(
                cls._information(
                    code="REG-DEF-012",
                    field="description",
                    message=(
                        "Active registry definition has no description."
                    ),
                    suggestion=(
                        "Add a concise description to improve "
                        "administrative and diagnostic clarity."
                    ),
                )
            )

    @classmethod
    def _validate_version(
        cls,
        definition: RegistryDefinition,
        collector: RegistryValidationCollector,
    ) -> None:
        if definition.version < 1:
            collector.add(
                cls._error(
                    code="REG-DEF-013",
                    field="version",
                    message=(
                        "Registry definition version must be at least 1."
                    ),
                    suggestion=(
                        "Assign a positive registry-definition version."
                    ),
                )
            )

    @classmethod
    def _validate_metadata(
        cls,
        definition: RegistryDefinition,
        collector: RegistryValidationCollector,
    ) -> None:
        metadata = definition.metadata

        if len(metadata) > MAXIMUM_REGISTRY_METADATA_ENTRIES:
            collector.add(
                cls._warning(
                    code="REG-DEF-014",
                    field="metadata",
                    message=(
                        "Registry metadata contains more than "
                        f"{MAXIMUM_REGISTRY_METADATA_ENTRIES} entries."
                    ),
                    suggestion=(
                        "Keep registry metadata concise and move large "
                        "structured data into a dedicated resource."
                    ),
                )
            )

        for key, value in metadata.items():
            field_path = f"metadata.{key}"

            if len(key) > MAXIMUM_REGISTRY_METADATA_KEY_LENGTH:
                collector.add(
                    cls._error(
                        code="REG-DEF-015",
                        field=field_path,
                        message=(
                            "Registry metadata key exceeds the maximum "
                            f"supported length of "
                            f"{MAXIMUM_REGISTRY_METADATA_KEY_LENGTH} "
                            "characters."
                        ),
                        suggestion=(
                            "Use a shorter stable metadata key."
                        ),
                    )
                )

            if isinstance(value, Mapping) and value is metadata:
                collector.add(
                    cls._error(
                        code="REG-DEF-016",
                        field=field_path,
                        message=(
                            "Registry metadata contains a direct "
                            "self-reference."
                        ),
                        suggestion=(
                            "Replace the self-reference with a stable "
                            "external reference value."
                        ),
                    )
                )

    @staticmethod
    def _normalize_comparison_values(
        values: Iterable[str],
        *,
        field_name: str,
        case_sensitive: bool,
    ) -> set[str]:
        if isinstance(values, (str, bytes)):
            raise TypeError(
                f"{field_name} must be an iterable of text values, "
                "not one text value."
            )

        normalized: set[str] = set()

        for value in values:
            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must contain only text values."
                )

            candidate = value.strip()

            if not candidate:
                continue

            normalized.add(
                candidate
                if case_sensitive
                else candidate.casefold()
            )

        return normalized

    @staticmethod
    def _error(
        *,
        code: str,
        field: str,
        message: str,
        suggestion: str | None = None,
    ) -> RegistryValidationMessage:
        return RegistryValidationMessage(
            severity=ValidationSeverity.ERROR,
            code=code,
            field=field,
            message=message,
            suggestion=suggestion,
        )

    @staticmethod
    def _warning(
        *,
        code: str,
        field: str,
        message: str,
        suggestion: str | None = None,
    ) -> RegistryValidationMessage:
        return RegistryValidationMessage(
            severity=ValidationSeverity.WARNING,
            code=code,
            field=field,
            message=message,
            suggestion=suggestion,
        )

    @staticmethod
    def _information(
        *,
        code: str,
        field: str,
        message: str,
        suggestion: str | None = None,
    ) -> RegistryValidationMessage:
        return RegistryValidationMessage(
            severity=ValidationSeverity.INFORMATION,
            code=code,
            field=field,
            message=message,
            suggestion=suggestion,
        )


__all__ = (
    "MAXIMUM_REGISTRY_DESCRIPTION_LENGTH",
    "MAXIMUM_REGISTRY_ID_LENGTH",
    "MAXIMUM_REGISTRY_METADATA_ENTRIES",
    "MAXIMUM_REGISTRY_METADATA_KEY_LENGTH",
    "MAXIMUM_REGISTRY_NAME_LENGTH",
    "MAXIMUM_REGISTRY_CODE_LENGTH",
    "MINIMUM_REGISTRY_CODE_LENGTH",
    "RegistryValidator",
)
