"""
============================================================
Nexa Provider Platform
File: shared/config/config_schema.py
Layer: Shared Configuration Foundation
Milestone: NPP-M003 — Configuration Engine
============================================================

Purpose
-------
Defines the immutable configuration schema used throughout
the Nexa Provider Platform.

The schema represents the validated configuration consumed by
the Runtime Engine, Logging Engine, Storage Engine,
Synchronization Engine, Provider Services, and future modules.

Validation is intentionally delegated to
config_validator.py.
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .environment import (
    DEFAULT_ENVIRONMENT,
    Environment,
)


class ConfigurationSchemaError(ValueError):
    """
    Raised when an invalid configuration object is created.
    """


@dataclass(frozen=True, slots=True)
class ConfigurationSchema:
    """
    Immutable platform configuration.

    Every module receives an instance of this class rather
    than reading environment variables directly.
    """

    environment: Environment = DEFAULT_ENVIRONMENT

    application_name: str = "Nexa Provider Platform"

    application_version: str = "0.1.0"

    debug: bool = True

    audit_enabled: bool = True

    strict_validation: bool = False

    simulation_enabled: bool = True

    storage_directory: Path = field(
        default_factory=lambda: Path("./storage")
    )

    log_directory: Path = field(
        default_factory=lambda: Path("./logs")
    )

    data_directory: Path = field(
        default_factory=lambda: Path("./storage/data")
    )

    configuration_directory: Path = field(
        default_factory=lambda: Path("./configs")
    )

    temporary_directory: Path = field(
        default_factory=lambda: Path("./storage/temp")
    )

    timezone: str = "UTC"

    encoding: str = "utf-8"

    maximum_log_file_size_mb: int = 50

    retained_log_files: int = 10

    maximum_worker_threads: int = 4

    metadata: dict[str, object] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        """
        Normalize values.

        Full business validation is performed by the
        Configuration Validator.
        """

        object.__setattr__(
            self,
            "environment",
            Environment.from_value(self.environment),
        )

    @property
    def production(self) -> bool:
        return self.environment.is_production

    @property
    def development(self) -> bool:
        return self.environment.is_development

    @property
    def testing(self) -> bool:
        return self.environment.is_testing

    @property
    def staging(self) -> bool:
        return self.environment.is_staging

    def directories(self) -> tuple[Path, ...]:
        """
        Return all managed platform directories.
        """

        return (
            self.storage_directory,
            self.log_directory,
            self.data_directory,
            self.configuration_directory,
            self.temporary_directory,
        )

    def to_dict(self) -> dict[str, object]:
        """
        Serialize configuration.
        """

        return {
            "environment": self.environment.value,
            "application_name": self.application_name,
            "application_version": self.application_version,
            "debug": self.debug,
            "audit_enabled": self.audit_enabled,
            "strict_validation": self.strict_validation,
            "simulation_enabled": self.simulation_enabled,
            "storage_directory": str(self.storage_directory),
            "log_directory": str(self.log_directory),
            "data_directory": str(self.data_directory),
            "configuration_directory": str(
                self.configuration_directory
            ),
            "temporary_directory": str(
                self.temporary_directory
            ),
            "timezone": self.timezone,
            "encoding": self.encoding,
            "maximum_log_file_size_mb": (
                self.maximum_log_file_size_mb
            ),
            "retained_log_files": self.retained_log_files,
            "maximum_worker_threads": (
                self.maximum_worker_threads
            ),
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(
        cls,
        values: dict[str, object],
    ) -> "ConfigurationSchema":
        """
        Construct a configuration from a dictionary.
        """

        values = dict(values)

        if "environment" in values:
            values["environment"] = Environment.from_value(
                values["environment"]
            )

        path_fields = (
            "storage_directory",
            "log_directory",
            "data_directory",
            "configuration_directory",
            "temporary_directory",
        )

        for field_name in path_fields:
            if field_name in values:
                values[field_name] = Path(
                    str(values[field_name])
                )

        return cls(**values)

    def summary(self) -> str:
        """
        Human-readable summary.
        """

        return (
            "========================================================\n"
            f"{self.application_name}\n"
            "Configuration Summary\n"
            "--------------------------------------------------------\n"
            f"Environment : {self.environment.label}\n"
            f"Version     : {self.application_version}\n"
            f"Debug       : {self.debug}\n"
            f"Audit       : {self.audit_enabled}\n"
            f"Simulation  : {self.simulation_enabled}\n"
            f"Validation  : {self.strict_validation}\n"
            f"Storage     : {self.storage_directory}\n"
            f"Logs        : {self.log_directory}\n"
            f"Data        : {self.data_directory}\n"
            f"Timezone    : {self.timezone}\n"
            "========================================================"
        )