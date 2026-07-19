"""
============================================================
Nexa Provider Platform
File: shared/config/config_loader.py
Layer: Shared Configuration Foundation
Milestone: NPP-M003 — Configuration Engine
============================================================

Purpose
-------
Loads, merges, normalizes, and validates platform configuration
before it is consumed by the Nexa Provider Platform.

Configuration may be assembled from:

1. ConfigurationSchema defaults
2. A JSON configuration file
3. Process environment variables
4. Explicit runtime overrides

The configuration sources are applied in that order.

Later sources take precedence over earlier sources:

Schema Defaults
        |
        v
JSON Configuration File
        |
        v
Environment Variables
        |
        v
Explicit Overrides
        |
        v
Normalized Configuration Values
        |
        v
ConfigurationSchema
        |
        v
ConfigurationValidator
        |
        v
Validated Configuration

Responsibilities
----------------
This module is responsible for:

- Reading JSON configuration files
- Reading supported environment variables
- Applying configuration precedence
- Rejecting unsupported configuration fields
- Converting raw values into schema-compatible values
- Converting directory values into pathlib.Path objects
- Converting environment names into Environment values
- Converting Boolean and integer values safely
- Merging metadata dictionaries
- Constructing ConfigurationSchema instances
- Calling ConfigurationValidator
- Returning structured load information

This module is not responsible for:

- Creating configured directories
- Initializing the Runtime Engine
- Initializing the Logging Engine
- Writing platform logs
- Modifying operating-system environment variables
- Persisting configuration changes
- Mutating ConfigurationSchema after construction

Configuration Precedence
------------------------
The final value for each field is selected according to the
following priority:

Explicit override
    Highest priority.

Environment variable
    Overrides JSON and defaults.

JSON configuration file
    Overrides schema defaults.

ConfigurationSchema default
    Lowest priority.

Metadata behaves slightly differently. Metadata dictionaries are
merged recursively by source precedence instead of replacing the
entire dictionary at every layer.

Environment Variable Naming
---------------------------
The default environment-variable prefix is:

NPP_

Examples:

NPP_ENVIRONMENT
NPP_APPLICATION_NAME
NPP_APPLICATION_VERSION
NPP_DEBUG
NPP_AUDIT_ENABLED
NPP_STRICT_VALIDATION
NPP_SIMULATION_ENABLED
NPP_STORAGE_DIRECTORY
NPP_LOG_DIRECTORY
NPP_DATA_DIRECTORY
NPP_CONFIGURATION_DIRECTORY
NPP_TEMPORARY_DIRECTORY
NPP_TIMEZONE
NPP_ENCODING
NPP_MAXIMUM_LOG_FILE_SIZE_MB
NPP_RETAINED_LOG_FILES
NPP_MAXIMUM_WORKER_THREADS
NPP_METADATA

NPP_METADATA must contain a JSON object when supplied.

Example:

NPP_METADATA={"service":"provider-api","region":"africa"}

Security Notes
--------------
The loader does not print configuration values and does not log
environment-variable contents.

Future sensitive settings must be handled by a dedicated secrets
layer rather than being placed inside general metadata.
============================================================
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from dataclasses import MISSING, dataclass, fields
from enum import Enum
from pathlib import Path
from typing import Final

from .config_schema import ConfigurationSchema
from .config_validator import (
    ConfigurationValidationResult,
    ConfigurationValidator,
    DEFAULT_CONFIGURATION_VALIDATOR,
)
from .environment import Environment, EnvironmentError


"""
============================================================
SECTION 1 — Configuration Loader Constants
============================================================

This section defines stable loader-wide constants.

DEFAULT_ENVIRONMENT_PREFIX
    Prefix used when reading platform environment variables.

SUPPORTED_CONFIGURATION_FIELDS
    Field names accepted by ConfigurationSchema.

PATH_CONFIGURATION_FIELDS
    Fields converted into pathlib.Path objects.

BOOLEAN_CONFIGURATION_FIELDS
    Fields converted into real Boolean values.

INTEGER_CONFIGURATION_FIELDS
    Fields converted into integer values.

TEXT_CONFIGURATION_FIELDS
    Fields that must remain text.

These collections prevent conversion rules from being repeated
throughout the loader.
============================================================
"""

DEFAULT_ENVIRONMENT_PREFIX: Final[str] = "NPP_"

SUPPORTED_CONFIGURATION_FIELDS: Final[frozenset[str]] = (
    frozenset(
        field_definition.name
        for field_definition in fields(ConfigurationSchema)
    )
)

PATH_CONFIGURATION_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "storage_directory",
        "log_directory",
        "data_directory",
        "configuration_directory",
        "temporary_directory",
    }
)

BOOLEAN_CONFIGURATION_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "debug",
        "audit_enabled",
        "strict_validation",
        "simulation_enabled",
    }
)

INTEGER_CONFIGURATION_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "maximum_log_file_size_mb",
        "retained_log_files",
        "maximum_worker_threads",
    }
)

TEXT_CONFIGURATION_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "application_name",
        "application_version",
        "timezone",
        "encoding",
    }
)

METADATA_FIELD: Final[str] = "metadata"

ENVIRONMENT_FIELD: Final[str] = "environment"

DEFAULT_JSON_ENCODING: Final[str] = "utf-8"

TRUE_BOOLEAN_VALUES: Final[frozenset[str]] = frozenset(
    {
        "1",
        "true",
        "yes",
        "y",
        "on",
        "enabled",
        "enable",
    }
)

FALSE_BOOLEAN_VALUES: Final[frozenset[str]] = frozenset(
    {
        "0",
        "false",
        "no",
        "n",
        "off",
        "disabled",
        "disable",
    }
)


"""
============================================================
SECTION 2 — Configuration Source
============================================================

ConfigurationSource identifies where a configuration value came
from.

This information supports:

- Diagnostics
- Administrative interfaces
- Testing
- Future configuration audit records
- Operator troubleshooting

The source names are stable and machine-readable.
============================================================
"""


class ConfigurationSource(str, Enum):
    """
    Supported configuration-value sources.
    """

    DEFAULT = "default"

    JSON_FILE = "json_file"

    ENVIRONMENT_VARIABLE = "environment_variable"

    OVERRIDE = "override"

    @property
    def label(self) -> str:
        """
        Return a human-readable source label.
        """

        return {
            ConfigurationSource.DEFAULT: "Schema Default",
            ConfigurationSource.JSON_FILE: (
                "JSON Configuration File"
            ),
            ConfigurationSource.ENVIRONMENT_VARIABLE: (
                "Environment Variable"
            ),
            ConfigurationSource.OVERRIDE: (
                "Explicit Override"
            ),
        }[self]


"""
============================================================
SECTION 3 — Configuration Loader Exceptions
============================================================

ConfigurationLoadError is the base exception for failures that
occur while loading or normalizing configuration.

Specialized exceptions provide clearer failure categories:

ConfigurationFileError
    The configuration file is missing, unreadable, malformed, or
    does not contain a JSON object.

ConfigurationValueError
    A supplied field value cannot be converted into the type
    required by ConfigurationSchema.

UnknownConfigurationFieldError
    A configuration source contains unsupported field names.

These exceptions represent loading failures.

Schema-policy failures are reported separately by
ConfigurationValidator.
============================================================
"""


class ConfigurationLoadError(ValueError):
    """
    Base exception raised by the Configuration Loader.
    """


class ConfigurationFileError(ConfigurationLoadError):
    """
    Raised when a configuration file cannot be loaded safely.
    """


class ConfigurationValueError(ConfigurationLoadError):
    """
    Raised when a raw configuration value cannot be normalized.
    """


class UnknownConfigurationFieldError(ConfigurationLoadError):
    """
    Raised when unsupported configuration fields are supplied.
    """

    def __init__(
        self,
        unknown_fields: set[str],
        *,
        source: ConfigurationSource,
    ) -> None:
        normalized_fields = tuple(
            sorted(unknown_fields)
        )

        self.unknown_fields = normalized_fields

        self.source = source

        joined_fields = ", ".join(normalized_fields)

        super().__init__(
            "Unsupported configuration field"
            f"{'s' if len(normalized_fields) != 1 else ''} "
            f"from {source.label}: {joined_fields}."
        )


"""
============================================================
SECTION 4 — Configuration Load Result
============================================================

ConfigurationLoadResult describes one completed load operation.

configuration
    Final immutable ConfigurationSchema.

validation
    Structured ConfigurationValidationResult.

sources
    Final source selected for each top-level field.

configuration_file
    JSON file used during loading, when applicable.

environment_prefix
    Prefix used to inspect environment variables.

The result allows startup code to consume the configuration while
administrative tools can inspect where each value originated.
============================================================
"""


@dataclass(frozen=True, slots=True)
class ConfigurationLoadResult:
    """
    Immutable result of one configuration load operation.
    """

    configuration: ConfigurationSchema

    validation: ConfigurationValidationResult

    sources: Mapping[str, ConfigurationSource]

    configuration_file: Path | None = None

    environment_prefix: str = DEFAULT_ENVIRONMENT_PREFIX

    def __post_init__(self) -> None:
        """
        Validate and normalize load-result values.
        """

        if not isinstance(
            self.configuration,
            ConfigurationSchema,
        ):
            raise TypeError(
                "configuration must be a ConfigurationSchema."
            )

        if not isinstance(
            self.validation,
            ConfigurationValidationResult,
        ):
            raise TypeError(
                "validation must be a "
                "ConfigurationValidationResult."
            )

        normalized_sources: dict[
            str,
            ConfigurationSource,
        ] = {}

        for field_name, source in self.sources.items():
            if not isinstance(field_name, str):
                raise TypeError(
                    "Configuration source keys must be text."
                )

            normalized_sources[field_name] = (
                ConfigurationSource(source)
            )

        object.__setattr__(
            self,
            "sources",
            normalized_sources,
        )

        if (
            self.configuration_file is not None
            and not isinstance(self.configuration_file, Path)
        ):
            object.__setattr__(
                self,
                "configuration_file",
                Path(str(self.configuration_file)),
            )

        if not isinstance(self.environment_prefix, str):
            raise TypeError(
                "environment_prefix must be text."
            )

    @property
    def valid(self) -> bool:
        """
        Return True when configuration validation succeeded.
        """

        return self.validation.valid

    @property
    def invalid(self) -> bool:
        """
        Return True when configuration validation failed.
        """

        return self.validation.invalid

    def source_for(
        self,
        field_name: str,
    ) -> ConfigurationSource | None:
        """
        Return the final source for one configuration field.
        """

        if not isinstance(field_name, str):
            raise TypeError(
                "field_name must be text."
            )

        return self.sources.get(
            field_name.strip()
        )

    def to_dict(self) -> dict[str, object]:
        """
        Serialize the configuration-load result.
        """

        return {
            "configuration": self.configuration.to_dict(),
            "validation": self.validation.to_dict(),
            "sources": {
                field_name: source.value
                for field_name, source
                in self.sources.items()
            },
            "configuration_file": (
                str(self.configuration_file)
                if self.configuration_file is not None
                else None
            ),
            "environment_prefix": self.environment_prefix,
        }


"""
============================================================
SECTION 5 — Configuration Loader
============================================================

ConfigurationLoader coordinates the complete loading pipeline.

The class is stateless between individual load operations except
for its validator and environment-variable prefix.

A shared loader may therefore be safely reused.

Main Public Methods
-------------------
load()
    Return the final ConfigurationSchema.

load_with_result()
    Return ConfigurationLoadResult containing the configuration,
    validation result, source map, and file information.

load_file()
    Load configuration from a JSON file with optional environment
    values and overrides.

load_defaults()
    Construct and validate the schema defaults.
============================================================
"""


class ConfigurationLoader:
    """
    Loads and validates Nexa Provider Platform configuration.
    """

    def __init__(
        self,
        *,
        validator: ConfigurationValidator | None = None,
        environment_prefix: str = DEFAULT_ENVIRONMENT_PREFIX,
    ) -> None:
        """
        Initialize the Configuration Loader.

        Parameters
        ----------
        validator:
            Validator used after ConfigurationSchema construction.
            The default validator is used when omitted.

        environment_prefix:
            Prefix used when reading process environment variables.
        """

        if validator is None:
            validator = DEFAULT_CONFIGURATION_VALIDATOR

        if not isinstance(
            validator,
            ConfigurationValidator,
        ):
            raise TypeError(
                "validator must be a ConfigurationValidator."
            )

        self._validator = validator

        self._environment_prefix = (
            self._normalize_environment_prefix(
                environment_prefix
            )
        )

    @property
    def validator(self) -> ConfigurationValidator:
        """
        Return the configured validator.
        """

        return self._validator

    @property
    def environment_prefix(self) -> str:
        """
        Return the normalized environment-variable prefix.
        """

        return self._environment_prefix
    """
============================================================
SECTION 6 — Primary Load API
============================================================

The primary load API accepts all supported configuration sources.

Parameters
----------
configuration_file
    Optional JSON configuration file.

use_environment
    Whether process environment variables should be read.

environment
    Optional environment mapping. This is mainly useful for tests.
    os.environ is used when omitted.

overrides
    Optional highest-priority configuration mapping.

validate
    Whether ConfigurationValidator should run.

raise_on_validation_error
    Whether invalid configuration should raise through the
    validator.

allow_missing_file
    Whether a supplied but missing JSON file should be ignored.

reject_unknown_fields
    Whether unsupported field names should raise an exception.

File loading and validation are enabled by default.
============================================================
    """

    def load(
        self,
        *,
        configuration_file: str | Path | None = None,
        use_environment: bool = True,
        environment: Mapping[str, object] | None = None,
        overrides: Mapping[str, object] | None = None,
        validate: bool = True,
        raise_on_validation_error: bool = True,
        allow_missing_file: bool = False,
        reject_unknown_fields: bool = True,
    ) -> ConfigurationSchema:
        """
        Load and return the final platform configuration.
        """

        result = self.load_with_result(
            configuration_file=configuration_file,
            use_environment=use_environment,
            environment=environment,
            overrides=overrides,
            validate=validate,
            raise_on_validation_error=(
                raise_on_validation_error
            ),
            allow_missing_file=allow_missing_file,
            reject_unknown_fields=reject_unknown_fields,
        )

        return result.configuration

    def load_with_result(
        self,
        *,
        configuration_file: str | Path | None = None,
        use_environment: bool = True,
        environment: Mapping[str, object] | None = None,
        overrides: Mapping[str, object] | None = None,
        validate: bool = True,
        raise_on_validation_error: bool = True,
        allow_missing_file: bool = False,
        reject_unknown_fields: bool = True,
    ) -> ConfigurationLoadResult:
        """
        Load configuration and return structured load information.
        """

        self._validate_load_options(
            use_environment=use_environment,
            validate=validate,
            raise_on_validation_error=(
                raise_on_validation_error
            ),
            allow_missing_file=allow_missing_file,
            reject_unknown_fields=reject_unknown_fields,
        )

        combined_values = self._default_values()

        source_map = {
            field_name: ConfigurationSource.DEFAULT
            for field_name in combined_values
        }

        normalized_configuration_file: Path | None = None

        if configuration_file is not None:
            normalized_configuration_file = Path(
                configuration_file
            ).expanduser()

            file_values = self._load_json_file(
                normalized_configuration_file,
                allow_missing=allow_missing_file,
            )

            file_values = self._prepare_source_values(
                file_values,
                source=ConfigurationSource.JSON_FILE,
                reject_unknown_fields=(
                    reject_unknown_fields
                ),
            )

            self._apply_source(
                target=combined_values,
                source_values=file_values,
                source=ConfigurationSource.JSON_FILE,
                source_map=source_map,
            )

        if use_environment:
            environment_values = self._load_environment_values(
                environment=environment,
            )

            environment_values = self._prepare_source_values(
                environment_values,
                source=(
                    ConfigurationSource.ENVIRONMENT_VARIABLE
                ),
                reject_unknown_fields=(
                    reject_unknown_fields
                ),
            )

            self._apply_source(
                target=combined_values,
                source_values=environment_values,
                source=(
                    ConfigurationSource.ENVIRONMENT_VARIABLE
                ),
                source_map=source_map,
            )

        if overrides is not None:
            override_values = self._copy_mapping(
                overrides,
                source=ConfigurationSource.OVERRIDE,
            )

            override_values = self._prepare_source_values(
                override_values,
                source=ConfigurationSource.OVERRIDE,
                reject_unknown_fields=(
                    reject_unknown_fields
                ),
            )

            self._apply_source(
                target=combined_values,
                source_values=override_values,
                source=ConfigurationSource.OVERRIDE,
                source_map=source_map,
            )

        normalized_values = self._normalize_values(
            combined_values
        )

        configuration = self._construct_schema(
            normalized_values
        )

        validation_result = self._validate_configuration(
            configuration,
            validate=validate,
            raise_on_validation_error=(
                raise_on_validation_error
            ),
        )

        return ConfigurationLoadResult(
            configuration=configuration,
            validation=validation_result,
            sources=source_map,
            configuration_file=normalized_configuration_file,
            environment_prefix=self.environment_prefix,
        )


    """
============================================================
SECTION 7 — Convenience Load Methods
============================================================

These methods provide narrower entry points for common startup
and testing scenarios.

load_defaults()
    Loads only ConfigurationSchema defaults.

load_file()
    Loads a JSON file and optionally applies environment values
    and overrides.

load_environment()
    Loads defaults plus environment variables.

load_overrides()
    Loads defaults plus an explicit override mapping.
============================================================
    """

    def load_defaults(
        self,
        *,
        validate: bool = True,
        raise_on_validation_error: bool = True,
    ) -> ConfigurationSchema:
        """
        Load and validate ConfigurationSchema defaults.
        """

        return self.load(
            use_environment=False,
            validate=validate,
            raise_on_validation_error=(
                raise_on_validation_error
            ),
        )

    def load_file(
        self,
        configuration_file: str | Path,
        *,
        use_environment: bool = True,
        environment: Mapping[str, object] | None = None,
        overrides: Mapping[str, object] | None = None,
        validate: bool = True,
        raise_on_validation_error: bool = True,
        allow_missing_file: bool = False,
        reject_unknown_fields: bool = True,
    ) -> ConfigurationSchema:
        """
        Load configuration from a JSON file.
        """

        return self.load(
            configuration_file=configuration_file,
            use_environment=use_environment,
            environment=environment,
            overrides=overrides,
            validate=validate,
            raise_on_validation_error=(
                raise_on_validation_error
            ),
            allow_missing_file=allow_missing_file,
            reject_unknown_fields=reject_unknown_fields,
        )

    def load_environment(
        self,
        *,
        environment: Mapping[str, object] | None = None,
        validate: bool = True,
        raise_on_validation_error: bool = True,
    ) -> ConfigurationSchema:
        """
        Load defaults and environment-variable values.
        """

        return self.load(
            use_environment=True,
            environment=environment,
            validate=validate,
            raise_on_validation_error=(
                raise_on_validation_error
            ),
        )

    def load_overrides(
        self,
        overrides: Mapping[str, object],
        *,
        validate: bool = True,
        raise_on_validation_error: bool = True,
        reject_unknown_fields: bool = True,
    ) -> ConfigurationSchema:
        """
        Load defaults and explicit overrides.
        """

        return self.load(
            use_environment=False,
            overrides=overrides,
            validate=validate,
            raise_on_validation_error=(
                raise_on_validation_error
            ),
            reject_unknown_fields=reject_unknown_fields,
        )


    """
============================================================
SECTION 8 — Load Option Validation
============================================================

This block validates loader controls before configuration sources
are accessed.

Failing early gives callers a clear programming error rather than
allowing invalid option values to affect the load pipeline.
============================================================
    """

    @staticmethod
    def _validate_load_options(
        *,
        use_environment: bool,
        validate: bool,
        raise_on_validation_error: bool,
        allow_missing_file: bool,
        reject_unknown_fields: bool,
    ) -> None:
        """
        Validate Boolean load controls.
        """

        options = {
            "use_environment": use_environment,
            "validate": validate,
            "raise_on_validation_error": (
                raise_on_validation_error
            ),
            "allow_missing_file": allow_missing_file,
            "reject_unknown_fields": (
                reject_unknown_fields
            ),
        }

        for option_name, option_value in options.items():
            if not isinstance(option_value, bool):
                raise TypeError(
                    f"{option_name} must be a Boolean value."
                )

        if (
            raise_on_validation_error
            and not validate
        ):
            raise ValueError(
                "raise_on_validation_error cannot be True "
                "when validation is disabled."
            )


    """
============================================================
SECTION 9 — Schema Default Extraction
============================================================

ConfigurationSchema defaults are the first configuration layer.

A fresh ConfigurationSchema instance is created and serialized so
default factories such as Path and metadata receive independent
values.

This prevents shared mutable defaults and keeps the loader aligned
with the schema's actual default definitions.
============================================================
    """

    @staticmethod
    def _default_values() -> dict[str, object]:
        """
        Return a mutable copy of ConfigurationSchema defaults.
        """

        try:
            default_configuration = ConfigurationSchema()
        except Exception as exc:
            raise ConfigurationLoadError(
                "ConfigurationSchema defaults could not be "
                f"constructed: {exc}."
            ) from exc

        values = default_configuration.to_dict()

        metadata = values.get(METADATA_FIELD)

        if isinstance(metadata, Mapping):
            values[METADATA_FIELD] = dict(metadata)

        return values


    """
============================================================
SECTION 10 — JSON Configuration File Loading
============================================================

The JSON file loader enforces the following rules:

- The path must identify a file.
- Missing files fail unless allow_missing_file is enabled.
- UTF-8 is used by default.
- Invalid JSON produces ConfigurationFileError.
- The top-level JSON value must be an object.
- Empty files are invalid.
- Byte-order-mark UTF-8 files are accepted.

Example JSON
------------
{
  "environment": "development",
  "application_name": "Nexa Provider Platform",
  "debug": true,
  "storage_directory": "./storage",
  "metadata": {
    "service": "provider-platform"
  }
}
============================================================
    """

    @staticmethod
    def _load_json_file(
        path: Path,
        *,
        allow_missing: bool,
    ) -> dict[str, object]:
        """
        Load a JSON configuration file.
        """

        if not isinstance(path, Path):
            raise TypeError(
                "path must be a pathlib.Path."
            )

        if path.exists() and not path.is_file():
            raise ConfigurationFileError(
                f"Configuration path is not a file: {path}."
            )

        if not path.exists():
            if allow_missing:
                return {}

            raise ConfigurationFileError(
                f"Configuration file does not exist: {path}."
            )

        try:
            raw_text = path.read_text(
                encoding="utf-8-sig"
            )
        except UnicodeDecodeError as exc:
            raise ConfigurationFileError(
                "Configuration file is not valid UTF-8: "
                f"{path}."
            ) from exc
        except OSError as exc:
            raise ConfigurationFileError(
                "Configuration file could not be read: "
                f"{path}. Reason: {exc}."
            ) from exc

        if not raw_text.strip():
            raise ConfigurationFileError(
                f"Configuration file is empty: {path}."
            )

        try:
            loaded_value = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise ConfigurationFileError(
                "Configuration file contains invalid JSON at "
                f"line {exc.lineno}, column {exc.colno}: "
                f"{path}. {exc.msg}."
            ) from exc

        if not isinstance(loaded_value, dict):
            raise ConfigurationFileError(
                "Configuration file must contain a JSON object "
                f"at its top level: {path}."
            )

        return dict(loaded_value)
        
    """
============================================================
SECTION 11 — Environment Variable Loading
============================================================

This section maps ConfigurationSchema fields to prefixed process
environment variables.

Field names are converted to uppercase.

Example:

application_name
        |
        v
NPP_APPLICATION_NAME

Only variables corresponding to supported schema fields are read.

Values remain raw until the normalization stage.
============================================================
    """

    def _load_environment_values(
        self,
        *,
        environment: Mapping[str, object] | None,
    ) -> dict[str, object]:
        """
        Read supported values from an environment mapping.
        """

        if environment is None:
            environment = os.environ

        if not isinstance(environment, Mapping):
            raise TypeError(
                "environment must be a mapping or None."
            )

        loaded_values: dict[str, object] = {}

        for field_name in SUPPORTED_CONFIGURATION_FIELDS:
            variable_name = self._environment_variable_name(
                field_name
            )

            if variable_name not in environment:
                continue

            raw_value = environment[variable_name]

            if raw_value is None:
                continue

            loaded_values[field_name] = raw_value

        return loaded_values

    def _environment_variable_name(
        self,
        field_name: str,
    ) -> str:
        """
        Return the environment-variable name for a field.
        """

        return (
            f"{self.environment_prefix}"
            f"{field_name.upper()}"
        )

    @staticmethod
    def _normalize_environment_prefix(
        prefix: str,
    ) -> str:
        """
        Normalize an environment-variable prefix.
        """

        if not isinstance(prefix, str):
            raise TypeError(
                "environment_prefix must be text."
            )

        normalized = prefix.strip().upper()

        if not normalized:
            raise ValueError(
                "environment_prefix cannot be empty."
            )

        if not normalized.endswith("_"):
            normalized = f"{normalized}_"

        if not all(
            character.isalnum() or character == "_"
            for character in normalized
        ):
            raise ValueError(
                "environment_prefix may contain only letters, "
                "numbers, and underscores."
            )

        return normalized


    """
============================================================
SECTION 12 — Source Mapping Preparation
============================================================

Every source mapping passes through this block before merging.

The block:

- Confirms the source is a mapping.
- Copies values into a plain dictionary.
- Confirms field names are text.
- Normalizes surrounding whitespace in field names.
- Detects unsupported configuration fields.
- Optionally rejects unknown fields.
- Removes unknown fields when rejection is disabled.

The loader never silently forwards unknown fields into
ConfigurationSchema.
============================================================
    """

    def _prepare_source_values(
        self,
        values: Mapping[str, object],
        *,
        source: ConfigurationSource,
        reject_unknown_fields: bool,
    ) -> dict[str, object]:
        """
        Prepare and filter one configuration source.
        """

        copied_values = self._copy_mapping(
            values,
            source=source,
        )

        unknown_fields = (
            set(copied_values)
            - set(SUPPORTED_CONFIGURATION_FIELDS)
        )

        if unknown_fields and reject_unknown_fields:
            raise UnknownConfigurationFieldError(
                unknown_fields,
                source=source,
            )

        for unknown_field in unknown_fields:
            copied_values.pop(
                unknown_field,
                None,
            )

        return copied_values

    @staticmethod
    def _copy_mapping(
        values: Mapping[str, object],
        *,
        source: ConfigurationSource,
    ) -> dict[str, object]:
        """
        Copy a source mapping and normalize its field names.
        """

        if not isinstance(values, Mapping):
            raise TypeError(
                f"{source.label} configuration must be a "
                "mapping."
            )

        copied: dict[str, object] = {}

        for field_name, value in values.items():
            if not isinstance(field_name, str):
                raise ConfigurationLoadError(
                    f"{source.label} configuration field names "
                    "must be text."
                )

            normalized_field = field_name.strip()

            if not normalized_field:
                raise ConfigurationLoadError(
                    f"{source.label} configuration contains an "
                    "empty field name."
                )

            if normalized_field in copied:
                raise ConfigurationLoadError(
                    f"{source.label} contains duplicate field "
                    f"name {normalized_field!r} after "
                    "normalization."
                )

            copied[normalized_field] = value

        return copied


    """
============================================================
SECTION 13 — Configuration Source Application
============================================================

This block applies one source to the accumulated configuration.

Normal fields replace earlier values.

Metadata dictionaries are recursively merged:

Default metadata
        |
        v
File metadata
        |
        v
Environment metadata
        |
        v
Override metadata

When both an earlier and later metadata value contain a dictionary
under the same key, those dictionaries are merged recursively.

When the later value is not a dictionary, it replaces the earlier
value.
============================================================
    """

    def _apply_source(
        self,
        *,
        target: dict[str, object],
        source_values: Mapping[str, object],
        source: ConfigurationSource,
        source_map: dict[str, ConfigurationSource],
    ) -> None:
        """
        Apply one configuration source to accumulated values.
        """

        for field_name, value in source_values.items():
            if field_name == METADATA_FIELD:
                current_metadata = target.get(
                    METADATA_FIELD,
                    {},
                )

                target[METADATA_FIELD] = (
                    self._merge_metadata(
                        current_metadata,
                        value,
                        source=source,
                    )
                )
            else:
                target[field_name] = value

            source_map[field_name] = source

    def _merge_metadata(
        self,
        earlier: object,
        later: object,
        *,
        source: ConfigurationSource,
    ) -> dict[str, object]:
        """
        Recursively merge two metadata dictionaries.
        """

        earlier_mapping = self._coerce_metadata_mapping(
            earlier,
            source=ConfigurationSource.DEFAULT,
        )

        later_mapping = self._coerce_metadata_mapping(
            later,
            source=source,
        )

        merged: dict[str, object] = {
            key: self._copy_metadata_value(value)
            for key, value in earlier_mapping.items()
        }

        for key, later_value in later_mapping.items():
            earlier_value = merged.get(key)

            if (
                isinstance(earlier_value, Mapping)
                and isinstance(later_value, Mapping)
            ):
                merged[key] = self._merge_metadata(
                    earlier_value,
                    later_value,
                    source=source,
                )
            else:
                merged[key] = self._copy_metadata_value(
                    later_value
                )

        return merged

    @staticmethod
    def _copy_metadata_value(
        value: object,
    ) -> object:
        """
        Copy common mutable metadata containers recursively.
        """

        if isinstance(value, Mapping):
            return {
                key: ConfigurationLoader._copy_metadata_value(
                    nested_value
                )
                for key, nested_value in value.items()
            }

        if isinstance(value, list):
            return [
                ConfigurationLoader._copy_metadata_value(
                    nested_value
                )
                for nested_value in value
            ]

        if isinstance(value, tuple):
            return tuple(
                ConfigurationLoader._copy_metadata_value(
                    nested_value
                )
                for nested_value in value
            )

        return value


    """
============================================================
SECTION 14 — Complete Value Normalization
============================================================

After all sources have been merged, every value is converted into
the type expected by ConfigurationSchema.

Conversion Rules
----------------
environment
    Converted with Environment.from_value().

Path fields
    Converted into pathlib.Path values.

Boolean fields
    Converted with strict Boolean parsing.

Integer fields
    Converted with strict integer parsing.

Text fields
    Must already be text.

metadata
    Must be a dictionary or a JSON object string.

Values are normalized only once, after precedence has selected the
final raw value.
============================================================
    """

    def _normalize_values(
        self,
        values: Mapping[str, object],
    ) -> dict[str, object]:
        """
        Normalize all final configuration values.
        """

        normalized: dict[str, object] = {}

        for field_name in SUPPORTED_CONFIGURATION_FIELDS:
            if field_name not in values:
                continue

            raw_value = values[field_name]

            if field_name == ENVIRONMENT_FIELD:
                normalized[field_name] = (
                    self._normalize_environment_value(
                        raw_value
                    )
                )

            elif field_name in PATH_CONFIGURATION_FIELDS:
                normalized[field_name] = (
                    self._normalize_path_value(
                        field_name,
                        raw_value,
                    )
                )

            elif field_name in BOOLEAN_CONFIGURATION_FIELDS:
                normalized[field_name] = (
                    self._normalize_boolean_value(
                        field_name,
                        raw_value,
                    )
                )

            elif field_name in INTEGER_CONFIGURATION_FIELDS:
                normalized[field_name] = (
                    self._normalize_integer_value(
                        field_name,
                        raw_value,
                    )
                )

            elif field_name in TEXT_CONFIGURATION_FIELDS:
                normalized[field_name] = (
                    self._normalize_text_value(
                        field_name,
                        raw_value,
                    )
                )

            elif field_name == METADATA_FIELD:
                normalized[field_name] = (
                    self._normalize_metadata_value(
                        raw_value
                    )
                )

            else:
                normalized[field_name] = raw_value

        return normalized


    """
============================================================
SECTION 15 — Environment Value Normalization
============================================================

Environment.from_value() remains the single source of truth for
environment aliases.

Accepted examples include:

development
dev
testing
test
staging
stage
production
prod
============================================================
    """

    @staticmethod
    def _normalize_environment_value(
        value: object,
    ) -> Environment:
        """
        Normalize the deployment environment.
        """

        if not isinstance(
            value,
            (
                str,
                Environment,
            ),
        ):
            raise ConfigurationValueError(
                "environment must be text or an Environment "
                "instance."
            )

        try:
            return Environment.from_value(value)
        except EnvironmentError as exc:
            raise ConfigurationValueError(
                str(exc)
            ) from exc


    """
============================================================
SECTION 16 — Path Value Normalization
============================================================

Path configuration accepts:

- pathlib.Path
- Non-empty text

User-home markers are expanded.

Relative paths remain relative inside ConfigurationSchema. This is
intentional because path resolution belongs to runtime
initialization and validation reporting.

The loader does not create or resolve directories.
============================================================
    """

    @staticmethod
    def _normalize_path_value(
        field_name: str,
        value: object,
    ) -> Path:
        """
        Normalize one path configuration value.
        """

        if isinstance(value, Path):
            path = value

        elif isinstance(value, str):
            normalized_text = value.strip()

            if not normalized_text:
                raise ConfigurationValueError(
                    f"{field_name} cannot be empty."
                )

            if "\x00" in normalized_text:
                raise ConfigurationValueError(
                    f"{field_name} cannot contain a null byte."
                )

            path = Path(normalized_text)

        else:
            raise ConfigurationValueError(
                f"{field_name} must be text or a pathlib.Path."
            )

        return path.expanduser()

    """
============================================================
SECTION 17 — Boolean Value Normalization
============================================================

Boolean fields accept:

Native Boolean values
    True
    False

True text values
    1
    true
    yes
    y
    on
    enabled
    enable

False text values
    0
    false
    no
    n
    off
    disabled
    disable

Integer values other than the native Boolean type are rejected.
This prevents accidental conversion such as bool(42) becoming
True.
============================================================
    """

    @staticmethod
    def _normalize_boolean_value(
        field_name: str,
        value: object,
    ) -> bool:
        """
        Normalize one Boolean configuration value.
        """

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized in TRUE_BOOLEAN_VALUES:
                return True

            if normalized in FALSE_BOOLEAN_VALUES:
                return False

        raise ConfigurationValueError(
            f"{field_name} must be a Boolean or one of the "
            "supported Boolean text values."
        )


    """
============================================================
SECTION 18 — Integer Value Normalization
============================================================

Integer fields accept:

- Native integers, excluding Boolean values
- Base-10 integer text

The loader rejects:

- Floating-point values
- Decimal strings
- Boolean values
- Empty text
- Text containing non-integer characters

Range rules are enforced by ConfigurationValidator.
============================================================
    """

    @staticmethod
    def _normalize_integer_value(
        field_name: str,
        value: object,
    ) -> int:
        """
        Normalize one integer configuration value.
        """

        if isinstance(value, bool):
            raise ConfigurationValueError(
                f"{field_name} must be an integer, not a "
                "Boolean value."
            )

        if isinstance(value, int):
            return value

        if isinstance(value, str):
            normalized = value.strip()

            if not normalized:
                raise ConfigurationValueError(
                    f"{field_name} cannot be empty."
                )

            try:
                return int(
                    normalized,
                    10,
                )
            except ValueError as exc:
                raise ConfigurationValueError(
                    f"{field_name} must contain a base-10 "
                    f"integer. Received {value!r}."
                ) from exc

        raise ConfigurationValueError(
            f"{field_name} must be an integer or integer text."
        )


    """
============================================================
SECTION 19 — Text Value Normalization
============================================================

Text fields must be actual strings.

The loader preserves internal whitespace and surrounding
whitespace. The validator may report surrounding whitespace as a
warning where appropriate.

Automatic conversion with str(value) is deliberately avoided
because it can hide configuration mistakes.
============================================================
    """

    @staticmethod
    def _normalize_text_value(
        field_name: str,
        value: object,
    ) -> str:
        """
        Normalize one text configuration value.
        """

        if not isinstance(value, str):
            raise ConfigurationValueError(
                f"{field_name} must be text."
            )

        return value


    """
============================================================
SECTION 20 — Metadata Value Normalization
============================================================

Metadata may be supplied as:

- A Python mapping
- A JSON object string

Environment-variable metadata is normally supplied as JSON text.

Example:

NPP_METADATA={"service":"registry","region":"africa"}

The top-level metadata value must always resolve to a dictionary.
Detailed JSON compatibility is enforced by ConfigurationValidator.
============================================================
    """

    def _normalize_metadata_value(
        self,
        value: object,
    ) -> dict[str, object]:
        """
        Normalize metadata into a dictionary.
        """

        return self._coerce_metadata_mapping(
            value,
            source=ConfigurationSource.OVERRIDE,
        )

    @staticmethod
    def _coerce_metadata_mapping(
        value: object,
        *,
        source: ConfigurationSource,
    ) -> dict[str, object]:
        """
        Convert a metadata value into a dictionary.
        """

        if isinstance(value, Mapping):
            return {
                key: ConfigurationLoader._copy_metadata_value(
                    nested_value
                )
                for key, nested_value in value.items()
            }

        if isinstance(value, str):
            normalized = value.strip()

            if not normalized:
                return {}

            try:
                parsed = json.loads(normalized)
            except json.JSONDecodeError as exc:
                raise ConfigurationValueError(
                    f"Metadata from {source.label} contains "
                    "invalid JSON at "
                    f"line {exc.lineno}, column {exc.colno}: "
                    f"{exc.msg}."
                ) from exc

            if not isinstance(parsed, dict):
                raise ConfigurationValueError(
                    f"Metadata from {source.label} must be a "
                    "JSON object."
                )

            return dict(parsed)

        raise ConfigurationValueError(
            f"Metadata from {source.label} must be a mapping "
            "or JSON object text."
        )


    """
============================================================
SECTION 21 — ConfigurationSchema Construction
============================================================

This block creates the final immutable ConfigurationSchema.

Unexpected constructor failures are wrapped in
ConfigurationLoadError so callers can distinguish configuration
assembly failures from unrelated runtime errors.
============================================================
    """

    @staticmethod
    def _construct_schema(
        values: Mapping[str, object],
    ) -> ConfigurationSchema:
        """
        Construct ConfigurationSchema from normalized values.
        """

        try:
            return ConfigurationSchema(
                **dict(values)
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ConfigurationLoadError(
                "ConfigurationSchema could not be constructed: "
                f"{exc}."
            ) from exc


    """
============================================================
SECTION 22 — Final Configuration Validation
============================================================

ConfigurationValidator remains responsible for business rules and
cross-field policy.

When validation is disabled, an empty valid result is returned.

When validation is enabled:

raise_on_validation_error = True
    validate_or_raise() is used.

raise_on_validation_error = False
    validate() returns errors without raising.

This separation supports both strict platform startup and
administrative configuration preview tools.
============================================================
    """

    def _validate_configuration(
        self,
        configuration: ConfigurationSchema,
        *,
        validate: bool,
        raise_on_validation_error: bool,
    ) -> ConfigurationValidationResult:
        """
        Validate the final ConfigurationSchema.
        """

        if not validate:
            return ConfigurationValidationResult()

        if raise_on_validation_error:
            return self.validator.validate_or_raise(
                configuration
            )

        return self.validator.validate(
            configuration
        )


    """
============================================================
SECTION 23 — Schema Inspection Helpers
============================================================

These helpers expose schema information without duplicating field
definitions.

They are useful for:

- Tests
- Administrative configuration interfaces
- Documentation tools
- Future command-line configuration inspection
============================================================
    """

    @staticmethod
    def supported_fields() -> tuple[str, ...]:
        """
        Return all supported configuration field names.
        """

        return tuple(
            sorted(SUPPORTED_CONFIGURATION_FIELDS)
        )

    def environment_variables(
        self,
    ) -> dict[str, str]:
        """
        Return field-to-environment-variable mappings.
        """

        return {
            field_name: self._environment_variable_name(
                field_name
            )
            for field_name
            in sorted(SUPPORTED_CONFIGURATION_FIELDS)
        }

    @staticmethod
    def schema_defaults() -> dict[str, object]:
        """
        Return a new dictionary of schema defaults.
        """

        return ConfigurationLoader._default_values()


    """
============================================================
SECTION 24 — Default Loader and Compatibility Alias
============================================================

DEFAULT_CONFIGURATION_LOADER is the shared loader used by modules
that do not require a custom validator or environment prefix.

ConfigLoader is retained as a concise compatibility alias.

Both names refer to the same production loader implementation.
============================================================
"""


DEFAULT_CONFIGURATION_LOADER = ConfigurationLoader()

ConfigLoader = ConfigurationLoader


"""
============================================================
SECTION 25 — Functional Convenience API
============================================================

These module-level functions support callers that prefer a simple
functional interface.

load_configuration()
    Load and return ConfigurationSchema.

load_configuration_with_result()
    Load and return ConfigurationLoadResult.

load_configuration_file()
    Load a specific JSON file.

load_default_configuration()
    Load schema defaults without environment variables.

All functions delegate to DEFAULT_CONFIGURATION_LOADER.
============================================================
"""


def load_configuration(
    *,
    configuration_file: str | Path | None = None,
    use_environment: bool = True,
    environment: Mapping[str, object] | None = None,
    overrides: Mapping[str, object] | None = None,
    validate: bool = True,
    raise_on_validation_error: bool = True,
    allow_missing_file: bool = False,
    reject_unknown_fields: bool = True,
) -> ConfigurationSchema:
    """
    Load configuration using the default loader.
    """

    return DEFAULT_CONFIGURATION_LOADER.load(
        configuration_file=configuration_file,
        use_environment=use_environment,
        environment=environment,
        overrides=overrides,
        validate=validate,
        raise_on_validation_error=(
            raise_on_validation_error
        ),
        allow_missing_file=allow_missing_file,
        reject_unknown_fields=reject_unknown_fields,
    )


def load_configuration_with_result(
    *,
    configuration_file: str | Path | None = None,
    use_environment: bool = True,
    environment: Mapping[str, object] | None = None,
    overrides: Mapping[str, object] | None = None,
    validate: bool = True,
    raise_on_validation_error: bool = True,
    allow_missing_file: bool = False,
    reject_unknown_fields: bool = True,
) -> ConfigurationLoadResult:
    """
    Load configuration and return structured load information.
    """

    return DEFAULT_CONFIGURATION_LOADER.load_with_result(
        configuration_file=configuration_file,
        use_environment=use_environment,
        environment=environment,
        overrides=overrides,
        validate=validate,
        raise_on_validation_error=(
            raise_on_validation_error
        ),
        allow_missing_file=allow_missing_file,
        reject_unknown_fields=reject_unknown_fields,
    )


def load_configuration_file(
    configuration_file: str | Path,
    *,
    use_environment: bool = True,
    environment: Mapping[str, object] | None = None,
    overrides: Mapping[str, object] | None = None,
    validate: bool = True,
    raise_on_validation_error: bool = True,
    allow_missing_file: bool = False,
    reject_unknown_fields: bool = True,
) -> ConfigurationSchema:
    """
    Load a JSON configuration file using the default loader.
    """

    return DEFAULT_CONFIGURATION_LOADER.load_file(
        configuration_file,
        use_environment=use_environment,
        environment=environment,
        overrides=overrides,
        validate=validate,
        raise_on_validation_error=(
            raise_on_validation_error
        ),
        allow_missing_file=allow_missing_file,
        reject_unknown_fields=reject_unknown_fields,
    )


def load_default_configuration(
    *,
    validate: bool = True,
    raise_on_validation_error: bool = True,
) -> ConfigurationSchema:
    """
    Load ConfigurationSchema defaults without environment values.
    """

    return DEFAULT_CONFIGURATION_LOADER.load_defaults(
        validate=validate,
        raise_on_validation_error=(
            raise_on_validation_error
        ),
    )
    
