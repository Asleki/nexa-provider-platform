
"""
Nexa Provider Platform
File: registries/validators/numbering_strategy_validator.py

Validates NumberingStrategy objects against platform policy.
"""

from __future__ import annotations

from collections.abc import Iterable

from registries.core.numbering_strategy import (
    NumberingMode,
    NumberingStrategy,
)

from .validation_collector import RegistryValidationCollector
from .validation_message import RegistryValidationMessage, ValidationSeverity
from .validation_result import RegistryValidationResult


class NumberingStrategyValidator:
    """Stateless validator for NumberingStrategy."""

    @classmethod
    def validate(
        cls,
        strategy: NumberingStrategy,
        *,
        existing_strategy_ids: Iterable[str] = (),
        existing_strategy_codes: Iterable[str] = (),
    ) -> RegistryValidationResult:
        if not isinstance(strategy, NumberingStrategy):
            raise TypeError(
                "strategy must be a NumberingStrategy."
            )

        collector = RegistryValidationCollector()

        ids = {
            v.strip()
            for v in existing_strategy_ids
            if isinstance(v, str) and v.strip()
        }
        codes = {
            v.strip().casefold()
            for v in existing_strategy_codes
            if isinstance(v, str) and v.strip()
        }

        if strategy.strategy_id in ids:
            collector.add(
                cls._msg(
                    ValidationSeverity.ERROR,
                    "NST-001",
                    "strategy_id",
                    "Strategy ID already exists.",
                    "Choose a unique strategy ID.",
                )
            )

        if strategy.strategy_code.casefold() in codes:
            collector.add(
                cls._msg(
                    ValidationSeverity.ERROR,
                    "NST-002",
                    "strategy_code",
                    "Strategy code already exists.",
                    "Choose a unique strategy code.",
                )
            )

        if (
            strategy.mode is NumberingMode.SEQUENTIAL
            and strategy.padding_length is None
        ):
            collector.add(
                cls._msg(
                    ValidationSeverity.INFORMATION,
                    "NST-003",
                    "padding_length",
                    "Sequential numbering has no padding length.",
                    "Specify padding if fixed-width identifiers are preferred.",
                )
            )

        if (
            strategy.mode is NumberingMode.UUID
            and (
                strategy.prefix is not None
                or strategy.suffix is not None
            )
        ):
            collector.add(
                cls._msg(
                    ValidationSeverity.WARNING,
                    "NST-004",
                    "mode",
                    "UUID strategy uses a prefix and/or suffix.",
                    "Confirm this matches the intended identifier format.",
                )
            )

        if len(strategy.metadata) > 100:
            collector.add(
                cls._msg(
                    ValidationSeverity.WARNING,
                    "NST-005",
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
    "NumberingStrategyValidator",
)
