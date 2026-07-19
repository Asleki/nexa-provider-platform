"""
============================================================
Nexa Provider Platform
File: shared/config/environment.py
Layer: Shared Configuration Foundation
Milestone: NPP-M003 — Configuration Engine
============================================================

Purpose
-------
Defines the supported platform deployment environments and
provides safe parsing and environment-specific behavior.

This file establishes a single source of truth for environment
names used across:

- Runtime configuration
- Logging
- Provider services
- Registries
- Storage
- Synchronization
- Simulation
- Testing
============================================================
"""

from __future__ import annotations

from enum import Enum


class EnvironmentError(ValueError):
    """
    Raised when an unsupported environment value is supplied.
    """


class Environment(str, Enum):
    """
    Supported Nexa Provider Platform environments.
    """

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

    @property
    def label(self) -> str:
        """
        Return a human-readable environment label.
        """

        return {
            Environment.DEVELOPMENT: "Development",
            Environment.TESTING: "Testing",
            Environment.STAGING: "Staging",
            Environment.PRODUCTION: "Production",
        }[self]

    @property
    def is_development(self) -> bool:
        """
        Return True when running in development.
        """

        return self is Environment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """
        Return True when running in testing.
        """

        return self is Environment.TESTING

    @property
    def is_staging(self) -> bool:
        """
        Return True when running in staging.
        """

        return self is Environment.STAGING

    @property
    def is_production(self) -> bool:
        """
        Return True when running in production.
        """

        return self is Environment.PRODUCTION

    @property
    def allows_debugging(self) -> bool:
        """
        Return True when verbose debugging is allowed.
        """

        return self in {
            Environment.DEVELOPMENT,
            Environment.TESTING,
        }

    @property
    def requires_strict_validation(self) -> bool:
        """
        Return True when strict configuration validation is required.
        """

        return self in {
            Environment.STAGING,
            Environment.PRODUCTION,
        }

    @property
    def allows_simulation(self) -> bool:
        """
        Return True when simulation activity is allowed.

        Production explicitly forbids simulation mode.
        """

        return self is not Environment.PRODUCTION

    @property
    def requires_persistent_storage(self) -> bool:
        """
        Return True when temporary in-memory storage is not acceptable.
        """

        return self in {
            Environment.STAGING,
            Environment.PRODUCTION,
        }

    @classmethod
    def from_value(
        cls,
        value: str | "Environment",
    ) -> "Environment":
        """
        Parse an Environment from text or return an existing instance.

        Accepted examples
        -----------------
        development
        DEVELOPMENT
        dev
        test
        staging
        prod
        production
        """

        if isinstance(value, cls):
            return value

        if not isinstance(value, str):
            raise EnvironmentError(
                "Environment value must be text or an Environment instance."
            )

        normalized = value.strip().lower()

        aliases = {
            "dev": cls.DEVELOPMENT,
            "development": cls.DEVELOPMENT,
            "test": cls.TESTING,
            "testing": cls.TESTING,
            "stage": cls.STAGING,
            "staging": cls.STAGING,
            "prod": cls.PRODUCTION,
            "production": cls.PRODUCTION,
        }

        environment = aliases.get(normalized)

        if environment is None:
            supported = ", ".join(
                item.value for item in cls
            )

            raise EnvironmentError(
                f"Unsupported environment {value!r}. "
                f"Supported environments: {supported}."
            )

        return environment

    @classmethod
    def default(cls) -> "Environment":
        """
        Return the default platform environment.
        """

        return cls.DEVELOPMENT

    @classmethod
    def all(cls) -> tuple["Environment", ...]:
        """
        Return all supported environments.
        """

        return tuple(cls)

    def __str__(self) -> str:
        """
        Return the canonical environment value.
        """

        return self.value


DEFAULT_ENVIRONMENT = Environment.default()