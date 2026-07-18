"""
============================================================
Nexa Provider Platform
File: shared/runtime/runtime_config.py
Layer: Shared Runtime Foundation
Milestone: NPP-M001 — Core Foundation
Engine: Runtime Engine
============================================================

Purpose
-------
Defines the operating configuration used by the Nexa Provider
Platform while it is running.

This file answers questions such as:

- Which environment is active?
- Is provider simulation allowed?
- Which storage backend should be used?
- Is audit recording enabled?
- How strict should validation be?
- Which country profile is being simulated?

Important
---------
This module does not start the platform and does not connect to
storage. It only creates and validates the configuration that
other platform components will use.

The configuration is immutable after creation. A new configuration
must be created when settings need to change.
============================================================
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping


class RuntimeEnvironment(str, Enum):
    """
    Environments supported by the Nexa Provider Platform.
    """

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class StorageBackend(str, Enum):
    """
    Storage backends understood by the runtime foundation.

    Only JSON is expected to be implemented during the first
    development milestone. The other values reserve stable names
    for later platform expansion.
    """

    MEMORY = "memory"
    JSON = "json"
    CSV = "csv"
    SUPABASE = "supabase"
    POSTGRESQL = "postgresql"


class LogLevel(str, Enum):
    """
    Supported platform logging levels.
    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RuntimeConfigurationError(ValueError):
    """
    Raised when runtime configuration is missing, unsupported,
    or internally inconsistent.
    """


def _read_text(
    source: Mapping[str, str],
    key: str,
    default: str,
) -> str:
    """
    Read and normalize a text configuration value.
    """

    value = source.get(key, default)

    if value is None:
        return default

    normalized = str(value).strip()

    return normalized if normalized else default


def _read_boolean(
    source: Mapping[str, str],
    key: str,
    default: bool,
) -> bool:
    """
    Read a boolean environment value.

    Accepted true values:
    true, 1, yes, on, enabled

    Accepted false values:
    false, 0, no, off, disabled
    """

    raw_value = source.get(key)

    if raw_value is None or not str(raw_value).strip():
        return default

    normalized = str(raw_value).strip().lower()

    true_values = {"true", "1", "yes", "on", "enabled"}
    false_values = {"false", "0", "no", "off", "disabled"}

    if normalized in true_values:
        return True

    if normalized in false_values:
        return False

    raise RuntimeConfigurationError(
        f"Invalid boolean value for {key}: {raw_value!r}"
    )


def _read_enum(
    source: Mapping[str, str],
    key: str,
    enum_type: type[Enum],
    default: Enum,
) -> Enum:
    """
    Read an enum value from the environment.
    """

    raw_value = source.get(key)

    if raw_value is None or not str(raw_value).strip():
        return default

    normalized = str(raw_value).strip().lower()

    try:
        return enum_type(normalized)
    except ValueError as error:
        allowed_values = ", ".join(
            str(member.value) for member in enum_type
        )

        raise RuntimeConfigurationError(
            f"Unsupported value for {key}: {raw_value!r}. "
            f"Allowed values: {allowed_values}."
        ) from error


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    """
    Immutable operating configuration for one NPP runtime.

    A RuntimeConfig object is created before the platform starts
    and is then shared with the other core engines.
    """

    platform_name: str
    platform_version: str

    environment: RuntimeEnvironment
    storage_backend: StorageBackend
    log_level: LogLevel

    simulation_enabled: bool
    audit_enabled: bool
    logging_enabled: bool
    strict_validation: bool

    country_code: str
    country_profile: str

    data_directory: Path

    @classmethod
    def development_defaults(cls) -> "RuntimeConfig":
        """
        Create a safe local-development configuration.

        This configuration:

        - enables simulation;
        - enables audit and logging;
        - uses local JSON storage;
        - uses strict validation;
        - stores development data under storage/data.
        """

        config = cls(
            platform_name="Nexa Provider Platform",
            platform_version="0.1.0-alpha",
            environment=RuntimeEnvironment.DEVELOPMENT,
            storage_backend=StorageBackend.JSON,
            log_level=LogLevel.DEBUG,
            simulation_enabled=True,
            audit_enabled=True,
            logging_enabled=True,
            strict_validation=True,
            country_code="SIM",
            country_profile="nexa-simulated-country",
            data_directory=Path("storage/data"),
        )

        config.validate()
        return config

    @classmethod
    def from_environment(
        cls,
        environment_variables: Mapping[str, str] | None = None,
    ) -> "RuntimeConfig":
        """
        Build runtime configuration from environment variables.

        The optional environment_variables argument makes this
        method easy to test without modifying the device's real
        environment.

        Supported environment variables
        -------------------------------
        NPP_PLATFORM_NAME
        NPP_PLATFORM_VERSION
        NPP_ENVIRONMENT
        NPP_STORAGE_BACKEND
        NPP_LOG_LEVEL
        NPP_SIMULATION_ENABLED
        NPP_AUDIT_ENABLED
        NPP_LOGGING_ENABLED
        NPP_STRICT_VALIDATION
        NPP_COUNTRY_CODE
        NPP_COUNTRY_PROFILE
        NPP_DATA_DIRECTORY
        """

        source = (
            environment_variables
            if environment_variables is not None
            else os.environ
        )

        environment = _read_enum(
            source=source,
            key="NPP_ENVIRONMENT",
            enum_type=RuntimeEnvironment,
            default=RuntimeEnvironment.DEVELOPMENT,
        )

        storage_backend = _read_enum(
            source=source,
            key="NPP_STORAGE_BACKEND",
            enum_type=StorageBackend,
            default=StorageBackend.JSON,
        )

        default_log_level = (
            LogLevel.DEBUG
            if environment
            in {
                RuntimeEnvironment.DEVELOPMENT,
                RuntimeEnvironment.TESTING,
            }
            else LogLevel.INFO
        )

        log_level = _read_enum(
            source=source,
            key="NPP_LOG_LEVEL",
            enum_type=LogLevel,
            default=default_log_level,
        )

        default_simulation_enabled = (
            environment != RuntimeEnvironment.PRODUCTION
        )

        config = cls(
            platform_name=_read_text(
                source,
                "NPP_PLATFORM_NAME",
                "Nexa Provider Platform",
            ),
            platform_version=_read_text(
                source,
                "NPP_PLATFORM_VERSION",
                "0.1.0-alpha",
            ),
            environment=environment,
            storage_backend=storage_backend,
            log_level=log_level,
            simulation_enabled=_read_boolean(
                source,
                "NPP_SIMULATION_ENABLED",
                default_simulation_enabled,
            ),
            audit_enabled=_read_boolean(
                source,
                "NPP_AUDIT_ENABLED",
                True,
            ),
            logging_enabled=_read_boolean(
                source,
                "NPP_LOGGING_ENABLED",
                True,
            ),
            strict_validation=_read_boolean(
                source,
                "NPP_STRICT_VALIDATION",
                True,
            ),
            country_code=_read_text(
                source,
                "NPP_COUNTRY_CODE",
                "SIM",
            ).upper(),
            country_profile=_read_text(
                source,
                "NPP_COUNTRY_PROFILE",
                "nexa-simulated-country",
            ).lower(),
            data_directory=Path(
                _read_text(
                    source,
                    "NPP_DATA_DIRECTORY",
                    "storage/data",
                )
            ),
        )

        config.validate()
        return config

    @property
    def is_development(self) -> bool:
        """
        Return True when the platform is running in development.
        """

        return self.environment == RuntimeEnvironment.DEVELOPMENT

    @property
    def is_testing(self) -> bool:
        """
        Return True when the platform is running automated tests.
        """

        return self.environment == RuntimeEnvironment.TESTING

    @property
    def is_production(self) -> bool:
        """
        Return True when the platform is running in production.
        """

        return self.environment == RuntimeEnvironment.PRODUCTION

    @property
    def uses_local_storage(self) -> bool:
        """
        Return True when the configured storage is device-local.
        """

        return self.storage_backend in {
            StorageBackend.MEMORY,
            StorageBackend.JSON,
            StorageBackend.CSV,
        }

    def validate(self) -> None:
        """
        Validate the complete runtime configuration.

        Raises
        ------
        RuntimeConfigurationError
            When any configuration rule is violated.
        """

        if not self.platform_name.strip():
            raise RuntimeConfigurationError(
                "Platform name cannot be empty."
            )

        if not self.platform_version.strip():
            raise RuntimeConfigurationError(
                "Platform version cannot be empty."
            )

        if not self.country_code.strip():
            raise RuntimeConfigurationError(
                "Country code cannot be empty."
            )

        if len(self.country_code) > 8:
            raise RuntimeConfigurationError(
                "Country code cannot exceed 8 characters."
            )

        if not self.country_profile.strip():
            raise RuntimeConfigurationError(
                "Country profile cannot be empty."
            )

        if not str(self.data_directory).strip():
            raise RuntimeConfigurationError(
                "Data directory cannot be empty."
            )

        if (
            self.environment == RuntimeEnvironment.PRODUCTION
            and self.simulation_enabled
        ):
            raise RuntimeConfigurationError(
                "Simulation cannot be enabled in production."
            )

        if (
            self.environment == RuntimeEnvironment.PRODUCTION
            and not self.audit_enabled
        ):
            raise RuntimeConfigurationError(
                "Audit recording must be enabled in production."
            )

        if (
            self.environment == RuntimeEnvironment.PRODUCTION
            and not self.strict_validation
        ):
            raise RuntimeConfigurationError(
                "Strict validation must be enabled in production."
            )

        if (
            self.environment == RuntimeEnvironment.PRODUCTION
            and self.storage_backend == StorageBackend.MEMORY
        ):
            raise RuntimeConfigurationError(
                "In-memory storage cannot be used in production."
            )

    def ensure_data_directory(self) -> Path:
        """
        Create the configured local data directory when necessary.

        The method only creates a directory for local storage
        backends. Remote storage backends do not require a local
        registry directory.

        Returns
        -------
        Path
            The configured data directory.
        """

        if self.uses_local_storage:
            self.data_directory.mkdir(
                parents=True,
                exist_ok=True,
            )

        return self.data_directory

    def to_safe_dict(self) -> dict[str, Any]:
        """
        Convert the configuration into a serializable dictionary.

        This representation is safe for logs and startup displays.
        Future secrets must never be added to this output.
        """

        result = asdict(self)

        result["environment"] = self.environment.value
        result["storage_backend"] = self.storage_backend.value
        result["log_level"] = self.log_level.value
        result["data_directory"] = str(self.data_directory)

        return result

    def startup_summary(self) -> str:
        """
        Produce a readable startup summary for developers.
        """

        simulation_status = (
            "Enabled" if self.simulation_enabled else "Disabled"
        )
        audit_status = "Enabled" if self.audit_enabled else "Disabled"
        logging_status = (
            "Enabled" if self.logging_enabled else "Disabled"
        )
        validation_mode = (
            "Strict" if self.strict_validation else "Standard"
        )

        return "\n".join(
            [
                "=" * 48,
                self.platform_name,
                f"Version: {self.platform_version}",
                f"Runtime: {self.environment.value.title()}",
                f"Storage: {self.storage_backend.value.upper()}",
                f"Simulation: {simulation_status}",
                f"Country profile: {self.country_profile}",
                f"Logging: {logging_status}",
                f"Audit: {audit_status}",
                f"Validation: {validation_mode}",
                "=" * 48,
            ]
        )


def load_runtime_config(
    environment_variables: Mapping[str, str] | None = None,
) -> RuntimeConfig:
    """
    Public helper used by the future bootstrap engine.

    Other modules should call this function rather than creating
    unvalidated configuration objects manually.
    """

    return RuntimeConfig.from_environment(environment_variables)