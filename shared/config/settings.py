"""
============================================================
Nexa Provider Platform
File: shared/config/settings.py
Layer: Shared Configuration Foundation
Milestone: NPP-M003 — Configuration Engine
============================================================

Purpose
-------
Provides the platform-wide configuration access layer used after
configuration has been loaded and validated.

This module sits above:

- environment.py
- config_schema.py
- config_validator.py
- config_loader.py

It provides a controlled, thread-safe settings registry so every
platform module can access the same immutable
ConfigurationSchema instance.

The settings layer is responsible for:

- Loading the initial platform configuration
- Storing the active immutable ConfigurationSchema
- Providing thread-safe configuration access
- Preventing accidental configuration replacement
- Supporting explicit configuration initialization
- Supporting controlled replacement when authorized
- Supporting test-only or administrative reset workflows
- Exposing configuration field access helpers
- Exposing configuration source information
- Exposing validation results
- Providing module-level convenience functions
- Providing a read-only settings proxy

The settings layer is not responsible for:

- Reading JSON directly
- Parsing environment variables directly
- Normalizing raw configuration values
- Validating configuration business rules directly
- Creating configured directories
- Starting the Runtime Engine
- Starting the Logging Engine
- Writing audit records
- Persisting configuration changes

Those responsibilities remain assigned to their respective
modules.

Configuration Flow
------------------
Configuration Sources
        |
        v
ConfigurationLoader
        |
        v
ConfigurationSchema
        |
        v
ConfigurationValidator
        |
        v
ConfigurationLoadResult
        |
        v
SettingsRegistry
        |
        v
Runtime Engine
Logging Engine
Storage Engine
Synchronization Engine
Provider Services
Registries
Future Platform Modules

Design Principles
-----------------
Single active configuration
    The platform should have one active configuration per Python
    process.

Immutable configuration
    ConfigurationSchema is frozen and cannot be changed in place.

Explicit initialization
    Production startup should initialize settings deliberately.

Thread-safe access
    Multiple platform services may safely read settings.

Controlled replacement
    Replacing active configuration requires explicit permission.

No import-time loading
    Importing this module does not read files or environment
    variables automatically.

Predictable testing
    Tests may use an isolated SettingsRegistry or explicitly reset
    the default registry.
============================================================
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from types import MappingProxyType
from typing import Final, Generic, TypeVar, overload

from .config_loader import (
    DEFAULT_CONFIGURATION_LOADER,
    ConfigurationLoadResult,
    ConfigurationLoader,
    ConfigurationSource,
)
from .config_schema import ConfigurationSchema
from .config_validator import ConfigurationValidationResult


"""
============================================================
SECTION 1 — Settings Constants
============================================================

This section defines settings-wide constants.

DEFAULT_SETTINGS_NAME
    Human-readable name assigned to the default process registry.

UNINITIALIZED_GENERATION
    Generation number used before any configuration is installed.

FIRST_SETTINGS_GENERATION
    Generation number assigned to the first successful
    initialization.

The generation counter changes whenever the active configuration
is replaced or the registry is reset.
============================================================
"""

DEFAULT_SETTINGS_NAME: Final[str] = "default"

UNINITIALIZED_GENERATION: Final[int] = 0

FIRST_SETTINGS_GENERATION: Final[int] = 1


"""
============================================================
SECTION 2 — Settings Exceptions
============================================================

SettingsError
    Base exception for settings-layer failures.

SettingsNotInitializedError
    Raised when configuration is requested before initialization.

SettingsAlreadyInitializedError
    Raised when initialization is attempted after configuration
    has already been installed without replacement permission.

SettingsReplacementError
    Raised when a replacement request violates registry policy.

UnknownSettingError
    Raised when a caller requests an unsupported configuration
    field.

SettingsStateError
    Raised when internal registry state is inconsistent.
============================================================
"""


class SettingsError(RuntimeError):
    """
    Base exception raised by the settings layer.
    """


class SettingsNotInitializedError(SettingsError):
    """
    Raised when active settings are requested before initialization.
    """


class SettingsAlreadyInitializedError(SettingsError):
    """
    Raised when settings are initialized more than once without
    explicit replacement permission.
    """


class SettingsReplacementError(SettingsError):
    """
    Raised when active settings cannot be replaced safely.
    """


class UnknownSettingError(SettingsError, KeyError):
    """
    Raised when a requested setting field does not exist.
    """


class SettingsStateError(SettingsError):
    """
    Raised when registry state becomes internally inconsistent.
    """


"""
============================================================
SECTION 3 — Settings Snapshot
============================================================

SettingsSnapshot captures the complete public state of a
SettingsRegistry at one point in time.

The snapshot includes:

- Registry name
- Initialization state
- Generation number
- Active configuration
- Validation result
- Configuration source map
- Configuration file
- Environment-variable prefix

Snapshots are immutable and safe to pass to diagnostics,
administrative interfaces, test assertions, and future runtime
status reports.
============================================================
"""


@dataclass(frozen=True, slots=True)
class SettingsSnapshot:
    """
    Immutable snapshot of settings-registry state.
    """

    registry_name: str

    initialized: bool

    generation: int

    configuration: ConfigurationSchema | None

    validation: ConfigurationValidationResult | None

    sources: Mapping[str, ConfigurationSource]

    configuration_file: Path | None

    environment_prefix: str | None

    def __post_init__(self) -> None:
        """
        Validate and normalize snapshot values.
        """

        if not isinstance(self.registry_name, str):
            raise TypeError(
                "registry_name must be text."
            )

        normalized_name = self.registry_name.strip()

        if not normalized_name:
            raise ValueError(
                "registry_name cannot be empty."
            )

        object.__setattr__(
            self,
            "registry_name",
            normalized_name,
        )

        if not isinstance(self.initialized, bool):
            raise TypeError(
                "initialized must be a Boolean value."
            )

        if (
            isinstance(self.generation, bool)
            or not isinstance(self.generation, int)
        ):
            raise TypeError(
                "generation must be an integer."
            )

        if self.generation < UNINITIALIZED_GENERATION:
            raise ValueError(
                "generation cannot be negative."
            )

        if (
            self.configuration is not None
            and not isinstance(
                self.configuration,
                ConfigurationSchema,
            )
        ):
            raise TypeError(
                "configuration must be a ConfigurationSchema "
                "or None."
            )

        if (
            self.validation is not None
            and not isinstance(
                self.validation,
                ConfigurationValidationResult,
            )
        ):
            raise TypeError(
                "validation must be a "
                "ConfigurationValidationResult or None."
            )

        normalized_sources: dict[
            str,
            ConfigurationSource,
        ] = {}

        for field_name, source in self.sources.items():
            if not isinstance(field_name, str):
                raise TypeError(
                    "Settings source names must be text."
                )

            normalized_sources[field_name] = (
                ConfigurationSource(source)
            )

        object.__setattr__(
            self,
            "sources",
            MappingProxyType(normalized_sources),
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

        if (
            self.environment_prefix is not None
            and not isinstance(self.environment_prefix, str)
        ):
            raise TypeError(
                "environment_prefix must be text or None."
            )

        if self.initialized:
            if self.configuration is None:
                raise ValueError(
                    "An initialized snapshot requires "
                    "configuration."
                )

            if self.validation is None:
                raise ValueError(
                    "An initialized snapshot requires "
                    "validation."
                )

            if self.generation < FIRST_SETTINGS_GENERATION:
                raise ValueError(
                    "An initialized snapshot requires a "
                    "positive generation."
                )

        else:
            if self.configuration is not None:
                raise ValueError(
                    "An uninitialized snapshot cannot contain "
                    "configuration."
                )

            if self.validation is not None:
                raise ValueError(
                    "An uninitialized snapshot cannot contain "
                    "validation."
                )

    @property
    def valid(self) -> bool:
        """
        Return True when initialized configuration is valid.
        """

        return bool(
            self.initialized
            and self.validation is not None
            and self.validation.valid
        )

    @property
    def invalid(self) -> bool:
        """
        Return True when initialized configuration is invalid.
        """

        return bool(
            self.initialized
            and self.validation is not None
            and self.validation.invalid
        )

    def source_for(
        self,
        field_name: str,
    ) -> ConfigurationSource | None:
        """
        Return the source selected for one configuration field.
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
        Serialize the settings snapshot.
        """

        return {
            "registry_name": self.registry_name,
            "initialized": self.initialized,
            "generation": self.generation,
            "valid": self.valid,
            "invalid": self.invalid,
            "configuration": (
                self.configuration.to_dict()
                if self.configuration is not None
                else None
            ),
            "validation": (
                self.validation.to_dict()
                if self.validation is not None
                else None
            ),
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

    def summary(self) -> str:
        """
        Return a human-readable settings snapshot summary.
        """

        lines = [
            "========================================================",
            "Nexa Provider Platform",
            "Settings Snapshot",
            "--------------------------------------------------------",
            f"Registry    : {self.registry_name}",
            f"Initialized : {self.initialized}",
            f"Generation  : {self.generation}",
        ]

        if self.configuration is not None:
            lines.extend(
                [
                    f"Application  : "
                    f"{self.configuration.application_name}",
                    f"Version      : "
                    f"{self.configuration.application_version}",
                    f"Environment  : "
                    f"{self.configuration.environment.label}",
                    f"Valid        : {self.valid}",
                ]
            )

        if self.configuration_file is not None:
            lines.append(
                f"Config File  : {self.configuration_file}"
            )

        lines.append(
            "========================================================"
        )

        return "\n".join(lines)


"""
============================================================
SECTION 4 — Settings Registry
============================================================

SettingsRegistry owns one active ConfigurationLoadResult.

It is the central settings state container used by the platform.

Thread Safety
-------------
All reads and writes involving registry state are protected by an
RLock.

ConfigurationSchema and ConfigurationLoadResult are immutable at
the settings boundary, so callers receive stable objects.

Initialization Rules
--------------------
First initialization
    Allowed.

Second initialization without replace=True
    Rejected.

Replacement with replace=True
    Allowed only when the new configuration is valid.

Reset
    Explicitly removes active configuration and advances the
    generation counter.

No automatic initialization occurs during module import.
============================================================
"""


class SettingsRegistry:
    """
    Thread-safe registry for active platform configuration.
    """

    def __init__(
        self,
        *,
        name: str = DEFAULT_SETTINGS_NAME,
        loader: ConfigurationLoader | None = None,
    ) -> None:
        """
        Initialize an empty settings registry.

        Parameters
        ----------
        name:
            Human-readable registry name.

        loader:
            ConfigurationLoader used for load-based initialization.
            The default loader is used when omitted.
        """

        if not isinstance(name, str):
            raise TypeError(
                "name must be text."
            )

        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError(
                "name cannot be empty."
            )

        if loader is None:
            loader = DEFAULT_CONFIGURATION_LOADER

        if not isinstance(loader, ConfigurationLoader):
            raise TypeError(
                "loader must be a ConfigurationLoader."
            )

        self._name = normalized_name

        self._loader = loader

        self._lock = RLock()

        self._load_result: ConfigurationLoadResult | None = None

        self._generation = UNINITIALIZED_GENERATION

    @property
    def name(self) -> str:
        """
        Return the registry name.
        """

        return self._name

    @property
    def loader(self) -> ConfigurationLoader:
        """
        Return the configured ConfigurationLoader.
        """

        return self._loader

    @property
    def initialized(self) -> bool:
        """
        Return True when active settings are installed.
        """

        with self._lock:
            return self._load_result is not None

    @property
    def generation(self) -> int:
        """
        Return the current registry generation.
        """

        with self._lock:
            return self._generation


    """
    ============================================================
    SECTION 5 — Load-Based Initialization
    ============================================================
    
    initialize() uses ConfigurationLoader to assemble, normalize, and
    validate settings.
    
    This is the normal platform startup path.
    
    The method accepts the same primary source controls as
    ConfigurationLoader.load_with_result().
    
    replace=False
        Protects active settings from accidental replacement.
    
    replace=True
        Explicitly authorizes replacement after the new configuration
        has loaded and validated successfully.
    
    Registry state is updated only after loading completes. A failed
    load leaves the previous active configuration untouched.
    ============================================================
    """

    def initialize(
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
        replace: bool = False,
    ) -> ConfigurationSchema:
        """
        Load and install active platform settings.
        """

        if not isinstance(replace, bool):
            raise TypeError(
                "replace must be a Boolean value."
            )

        with self._lock:
            if self._load_result is not None and not replace:
                raise SettingsAlreadyInitializedError(
                    f"Settings registry {self.name!r} is already "
                    "initialized. Pass replace=True only when "
                    "replacement is intentional."
                )

        load_result = self.loader.load_with_result(
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

        if load_result.invalid:
            raise SettingsReplacementError(
                "Invalid configuration cannot be installed in "
                f"settings registry {self.name!r}."
            )

        self.install_result(
            load_result,
            replace=replace,
        )

        return load_result.configuration


    """
    ============================================================
    SECTION 6 — Direct Configuration Installation
    ============================================================
    
    install_configuration() supports cases where a validated
    ConfigurationSchema already exists.
    
    Examples:
    
    - Unit tests
    - Embedded platform startup
    - Configuration received from a trusted bootstrap layer
    - Administrative tooling
    
    The configuration is still validated by the registry's loader
    validator before installation.
    
    Source information defaults to ConfigurationSource.OVERRIDE
    because the schema was supplied directly.
    ============================================================
    """

    def install_configuration(
        self,
        configuration: ConfigurationSchema,
        *,
        replace: bool = False,
        sources: Mapping[
            str,
            ConfigurationSource,
        ] | None = None,
        configuration_file: str | Path | None = None,
    ) -> ConfigurationSchema:
        """
        Validate and install an existing ConfigurationSchema.
        """

        if not isinstance(
            configuration,
            ConfigurationSchema,
        ):
            raise TypeError(
                "configuration must be a ConfigurationSchema."
            )

        if not isinstance(replace, bool):
            raise TypeError(
                "replace must be a Boolean value."
            )

        validation = self.loader.validator.validate_or_raise(
            configuration
        )

        if sources is None:
            sources = {
                field_name: ConfigurationSource.OVERRIDE
                for field_name
                in self.loader.supported_fields()
            }

        normalized_file = (
            Path(configuration_file).expanduser()
            if configuration_file is not None
            else None
        )

        load_result = ConfigurationLoadResult(
            configuration=configuration,
            validation=validation,
            sources=sources,
            configuration_file=normalized_file,
            environment_prefix=self.loader.environment_prefix,
        )

        self.install_result(
            load_result,
            replace=replace,
        )

        return configuration


    """
    ============================================================
    SECTION 7 — Load Result Installation
    ============================================================
    
    install_result() is the lowest-level installation method.
    
    It accepts a complete ConfigurationLoadResult and applies registry
    replacement policy.
    
    The result must already be valid.
    
    State installation is atomic while the registry lock is held.
    ============================================================
    """

    def install_result(
        self,
        load_result: ConfigurationLoadResult,
        *,
        replace: bool = False,
    ) -> None:
        """
        Install a complete ConfigurationLoadResult.
        """

        if not isinstance(
            load_result,
            ConfigurationLoadResult,
        ):
            raise TypeError(
                "load_result must be a ConfigurationLoadResult."
            )

        if not isinstance(replace, bool):
            raise TypeError(
                "replace must be a Boolean value."
            )

        if load_result.invalid:
            raise SettingsReplacementError(
                "A ConfigurationLoadResult containing validation "
                "errors cannot be installed."
            )

        with self._lock:
            if self._load_result is not None and not replace:
                raise SettingsAlreadyInitializedError(
                    f"Settings registry {self.name!r} is already "
                    "initialized."
                )

            self._load_result = load_result

            if self._generation < FIRST_SETTINGS_GENERATION:
                self._generation = FIRST_SETTINGS_GENERATION
            else:
                self._generation += 1


    """
    ============================================================
    SECTION 8 — Active Configuration Access
    ============================================================
    
    These methods expose active settings.
    
    get()
        Returns the active ConfigurationSchema.
    
    get_result()
        Returns the complete ConfigurationLoadResult.
    
    get_validation()
        Returns the active validation result.
    
    get_source()
        Returns the selected source for one configuration field.
    
    All methods fail clearly when the registry is uninitialized.
    ============================================================
    """

    def get(self) -> ConfigurationSchema:
        """
        Return the active ConfigurationSchema.
        """

        with self._lock:
            load_result = self._require_load_result()

            return load_result.configuration

    def get_result(self) -> ConfigurationLoadResult:
        """
        Return the active ConfigurationLoadResult.
        """

        with self._lock:
            return self._require_load_result()

    def get_validation(
        self,
    ) -> ConfigurationValidationResult:
        """
        Return the active validation result.
        """

        with self._lock:
            load_result = self._require_load_result()

            return load_result.validation

    def get_source(
        self,
        field_name: str,
    ) -> ConfigurationSource | None:
        """
        Return the active source for one field.
        """

        if not isinstance(field_name, str):
            raise TypeError(
                "field_name must be text."
            )

        normalized_field = field_name.strip()

        if not normalized_field:
            raise ValueError(
                "field_name cannot be empty."
            )

        with self._lock:
            load_result = self._require_load_result()

            return load_result.source_for(
                normalized_field
            )


    """
    ============================================================
    SECTION 9 — Individual Setting Access
    ============================================================
    
    get_value() retrieves one field from the active
    ConfigurationSchema.
    
    The method verifies that the requested field belongs to the
    schema.
    
    A default may be supplied for convenience. When no default is
    supplied, an unknown field raises UnknownSettingError.
    
    The sentinel object distinguishes:
    
    - No default supplied
    - default=None supplied intentionally
    ============================================================
    """

    _NO_DEFAULT: Final[object] = object()

    @overload
    def get_value(
        self,
        field_name: str,
    ) -> object:
        ...

    @overload
    def get_value(
        self,
        field_name: str,
        default: object,
    ) -> object:
        ...

    def get_value(
        self,
        field_name: str,
        default: object = _NO_DEFAULT,
    ) -> object:
        """
        Return one active configuration field.
        """

        if not isinstance(field_name, str):
            raise TypeError(
                "field_name must be text."
            )

        normalized_field = field_name.strip()

        if not normalized_field:
            raise ValueError(
                "field_name cannot be empty."
            )

        configuration = self.get()

        if hasattr(configuration, normalized_field):
            return getattr(
                configuration,
                normalized_field,
            )

        if default is not self._NO_DEFAULT:
            return default

        raise UnknownSettingError(
            f"Unknown configuration field "
            f"{normalized_field!r}."
        )

    def require_value(
        self,
        field_name: str,
    ) -> object:
        """
        Return one setting and reject None or empty text.
        """

        value = self.get_value(field_name)

        if value is None:
            raise SettingsError(
                f"Required setting {field_name!r} is None."
            )

        if isinstance(value, str) and not value.strip():
            raise SettingsError(
                f"Required setting {field_name!r} is empty."
            )

        return value

    def contains(
        self,
        field_name: str,
    ) -> bool:
        """
        Return True when the schema exposes the field.
        """

        if not isinstance(field_name, str):
            raise TypeError(
                "field_name must be text."
            )

        normalized_field = field_name.strip()

        if not normalized_field:
            return False

        configuration = self.get()

        return hasattr(
            configuration,
            normalized_field,
        )


    """
    ============================================================
    SECTION 10 — Settings Snapshot Creation
    ============================================================
    
    snapshot() returns an immutable representation of current registry
    state.
    
    Snapshots may be created before or after initialization.
    
    Before initialization:
        configuration and validation are None.
    
    After initialization:
        configuration, validation, sources, and file information are
        included.
    ============================================================
    """

    def snapshot(self) -> SettingsSnapshot:
        """
        Return an immutable settings-registry snapshot.
        """

        with self._lock:
            if self._load_result is None:
                return SettingsSnapshot(
                    registry_name=self.name,
                    initialized=False,
                    generation=self._generation,
                    configuration=None,
                    validation=None,
                    sources={},
                    configuration_file=None,
                    environment_prefix=(
                        self.loader.environment_prefix
                    ),
                )

            return SettingsSnapshot(
                registry_name=self.name,
                initialized=True,
                generation=self._generation,
                configuration=(
                    self._load_result.configuration
                ),
                validation=self._load_result.validation,
                sources=self._load_result.sources,
                configuration_file=(
                    self._load_result.configuration_file
                ),
                environment_prefix=(
                    self._load_result.environment_prefix
                ),
            )


    """
    ============================================================
    SECTION 11 — Controlled Reset
    ============================================================
    
    reset() removes active settings.
    
    This operation is intended for:
    
    - Automated tests
    - Controlled application reinitialization
    - Administrative maintenance workflows
    
    Runtime services should not reset configuration casually after
    startup because other components may already hold references to
    the previous immutable ConfigurationSchema.
    
    The generation counter advances when initialized state is reset.
    ============================================================
    """

    def reset(self) -> bool:
        """
        Remove active settings.

        Returns True when initialized settings were removed.
        Returns False when the registry was already empty.
        """

        with self._lock:
            if self._load_result is None:
                return False

            self._load_result = None

            self._generation += 1

            return True


    """
    ============================================================
    SECTION 12 — Internal Registry State Guard
    ============================================================
    
    _require_load_result() centralizes the uninitialized-state check.
    
    Keeping this check in one method ensures all access paths use the
    same exception type and message.
    ============================================================
    """

    def _require_load_result(
        self,
    ) -> ConfigurationLoadResult:
        """
        Return active load result or raise when uninitialized.
        """

        if self._load_result is None:
            raise SettingsNotInitializedError(
                f"Settings registry {self.name!r} has not been "
                "initialized."
            )

        return self._load_result


    """
    ============================================================
    SECTION 13 — Read-Only Settings Proxy
    ============================================================
    
    SettingsProxy provides convenient attribute-style access to the
    active ConfigurationSchema.
    
    Example:
    
    settings.environment
    settings.application_name
    settings.storage_directory
    settings.debug
    
    The proxy does not store configuration itself. Every access is
    resolved through its SettingsRegistry.
    
    This ensures replacement and reset behavior remain visible to
    future reads.
    
    Assignments are not supported.
    ============================================================
    """

class SettingsProxy:
    """
    Read-only proxy for active platform configuration.
    """

    __slots__ = (
        "_registry",
    )

    def __init__(
        self,
        registry: SettingsRegistry,
    ) -> None:
        if not isinstance(registry, SettingsRegistry):
            raise TypeError(
                "registry must be a SettingsRegistry."
            )

        object.__setattr__(
            self,
            "_registry",
            registry,
        )

    @property
    def registry(self) -> SettingsRegistry:
        """
        Return the backing SettingsRegistry.
        """

        return object.__getattribute__(
            self,
            "_registry",
        )

    @property
    def initialized(self) -> bool:
        """
        Return True when backing settings are initialized.
        """

        return self.registry.initialized

    @property
    def generation(self) -> int:
        """
        Return the backing registry generation.
        """

        return self.registry.generation

    @property
    def configuration(self) -> ConfigurationSchema:
        """
        Return the active ConfigurationSchema.
        """

        return self.registry.get()

    @property
    def validation(
        self,
    ) -> ConfigurationValidationResult:
        """
        Return the active validation result.
        """

        return self.registry.get_validation()

    def source_for(
        self,
        field_name: str,
    ) -> ConfigurationSource | None:
        """
        Return the source selected for one field.
        """

        return self.registry.get_source(field_name)

    def snapshot(self) -> SettingsSnapshot:
        """
        Return the current settings snapshot.
        """

        return self.registry.snapshot()

    def to_dict(self) -> dict[str, object]:
        """
        Serialize the active ConfigurationSchema.
        """

        return self.configuration.to_dict()

    def summary(self) -> str:
        """
        Return the active configuration summary.
        """

        return self.configuration.summary()

    def __getattr__(
        self,
        field_name: str,
    ) -> object:
        """
        Forward unknown public attributes to ConfigurationSchema.
        """

        if field_name.startswith("_"):
            raise AttributeError(field_name)

        try:
            return self.registry.get_value(field_name)
        except UnknownSettingError as exc:
            raise AttributeError(field_name) from exc

    def __setattr__(
        self,
        field_name: str,
        value: object,
    ) -> None:
        """
        Reject settings mutation through the proxy.
        """

        raise AttributeError(
            "SettingsProxy is read-only. Replace the active "
            "ConfigurationSchema through SettingsRegistry when "
            "explicit reconfiguration is required."
        )

    def __dir__(self) -> list[str]:
        """
        Return proxy and schema field names for inspection tools.
        """

        names = set(
            super().__dir__()
        )

        names.update(
            self.registry.loader.supported_fields()
        )

        return sorted(names)

    def __repr__(self) -> str:
        """
        Return a concise developer representation.
        """

        if not self.initialized:
            return (
                f"{self.__class__.__name__}("
                f"registry={self.registry.name!r}, "
                "initialized=False)"
            )

        configuration = self.configuration

        return (
            f"{self.__class__.__name__}("
            f"registry={self.registry.name!r}, "
            "initialized=True, "
            f"environment="
            f"{configuration.environment.value!r}, "
            f"application="
            f"{configuration.application_name!r})"
        )


"""
============================================================
SECTION 14 — Settings Mapping View
============================================================

SettingsMapping provides a read-only Mapping interface over the
active configuration.

This supports components that expect dictionary-like access while
preserving ConfigurationSchema as the source of truth.

Example:

settings_mapping["environment"]
settings_mapping.get("timezone")
list(settings_mapping)
============================================================
"""


class SettingsMapping(Mapping[str, object]):
    """
    Read-only mapping view of active settings.
    """

    def __init__(
        self,
        registry: SettingsRegistry,
    ) -> None:
        if not isinstance(registry, SettingsRegistry):
            raise TypeError(
                "registry must be a SettingsRegistry."
            )

        self._registry = registry

    @property
    def registry(self) -> SettingsRegistry:
        """
        Return the backing registry.
        """

        return self._registry

    def __getitem__(
        self,
        field_name: str,
    ) -> object:
        """
        Return one configuration field.
        """

        try:
            return self.registry.get_value(field_name)
        except UnknownSettingError as exc:
            raise KeyError(field_name) from exc

    def __iter__(self) -> Iterator[str]:
        """
        Iterate over supported configuration field names.
        """

        return iter(
            self.registry.loader.supported_fields()
        )

    def __len__(self) -> int:
        """
        Return the number of supported configuration fields.
        """

        return len(
            self.registry.loader.supported_fields()
        )

    def to_dict(self) -> dict[str, object]:
        """
        Serialize active settings into a dictionary.
        """

        return self.registry.get().to_dict()


"""
============================================================
SECTION 15 — Default Settings Objects
============================================================

DEFAULT_SETTINGS_REGISTRY
    Process-wide default settings registry.

settings
    Attribute-style read-only proxy.

settings_mapping
    Dictionary-style read-only mapping view.

Importing these objects does not initialize configuration.
============================================================
"""


DEFAULT_SETTINGS_REGISTRY = SettingsRegistry(
    name=DEFAULT_SETTINGS_NAME,
    loader=DEFAULT_CONFIGURATION_LOADER,
)

settings = SettingsProxy(
    DEFAULT_SETTINGS_REGISTRY
)

settings_mapping = SettingsMapping(
    DEFAULT_SETTINGS_REGISTRY
)
"""
============================================================
SECTION 16 — Default Registry Initialization API
============================================================

initialize_settings() initializes the process-wide default
registry.

This is the recommended startup function for the Nexa Provider
Platform.

Example
-------
configuration = initialize_settings(
    configuration_file="./configs/platform.json",
)

Environment values and explicit overrides may also be supplied.
============================================================
"""


def initialize_settings(
    *,
    configuration_file: str | Path | None = None,
    use_environment: bool = True,
    environment: Mapping[str, object] | None = None,
    overrides: Mapping[str, object] | None = None,
    validate: bool = True,
    raise_on_validation_error: bool = True,
    allow_missing_file: bool = False,
    reject_unknown_fields: bool = True,
    replace: bool = False,
) -> ConfigurationSchema:
    """
    Initialize the default settings registry.
    """

    return DEFAULT_SETTINGS_REGISTRY.initialize(
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
        replace=replace,
    )


"""
============================================================
SECTION 17 — Direct Default Configuration Installation
============================================================

install_settings() installs an existing ConfigurationSchema into
the default registry.

The supplied configuration is validated before installation.
============================================================
"""


def install_settings(
    configuration: ConfigurationSchema,
    *,
    replace: bool = False,
    sources: Mapping[
        str,
        ConfigurationSource,
    ] | None = None,
    configuration_file: str | Path | None = None,
) -> ConfigurationSchema:
    """
    Install an existing configuration into the default registry.
    """

    return DEFAULT_SETTINGS_REGISTRY.install_configuration(
        configuration,
        replace=replace,
        sources=sources,
        configuration_file=configuration_file,
    )


"""
============================================================
SECTION 18 — Default Settings Access API
============================================================

These functions provide a functional access style for modules that
do not use the SettingsProxy.

get_settings()
    Return active ConfigurationSchema.

get_settings_result()
    Return active ConfigurationLoadResult.

get_settings_validation()
    Return active ConfigurationValidationResult.

get_setting()
    Return one configuration field.

require_setting()
    Return one non-empty configuration field.

get_setting_source()
    Return the selected source for one field.
============================================================
"""


def get_settings() -> ConfigurationSchema:
    """
    Return active default platform settings.
    """

    return DEFAULT_SETTINGS_REGISTRY.get()


def get_settings_result() -> ConfigurationLoadResult:
    """
    Return the active default ConfigurationLoadResult.
    """

    return DEFAULT_SETTINGS_REGISTRY.get_result()


def get_settings_validation(
) -> ConfigurationValidationResult:
    """
    Return the active default validation result.
    """

    return DEFAULT_SETTINGS_REGISTRY.get_validation()


@overload
def get_setting(
    field_name: str,
) -> object:
    ...


@overload
def get_setting(
    field_name: str,
    default: object,
) -> object:
    ...


def get_setting(
    field_name: str,
    default: object = SettingsRegistry._NO_DEFAULT,
) -> object:
    """
    Return one field from active default settings.
    """

    if default is SettingsRegistry._NO_DEFAULT:
        return DEFAULT_SETTINGS_REGISTRY.get_value(
            field_name
        )

    return DEFAULT_SETTINGS_REGISTRY.get_value(
        field_name,
        default,
    )


def require_setting(
    field_name: str,
) -> object:
    """
    Return one required field from active default settings.
    """

    return DEFAULT_SETTINGS_REGISTRY.require_value(
        field_name
    )


def get_setting_source(
    field_name: str,
) -> ConfigurationSource | None:
    """
    Return the selected source for one default setting.
    """

    return DEFAULT_SETTINGS_REGISTRY.get_source(
        field_name
    )


"""
============================================================
SECTION 19 — Default Settings State API
============================================================

is_settings_initialized()
    Reports whether default settings are active.

get_settings_generation()
    Returns the current default registry generation.

get_settings_snapshot()
    Returns an immutable state snapshot.

reset_settings()
    Clears the default registry explicitly.
============================================================
"""


def is_settings_initialized() -> bool:
    """
    Return True when default settings are initialized.
    """

    return DEFAULT_SETTINGS_REGISTRY.initialized


def get_settings_generation() -> int:
    """
    Return the default registry generation.
    """

    return DEFAULT_SETTINGS_REGISTRY.generation


def get_settings_snapshot() -> SettingsSnapshot:
    """
    Return the default settings snapshot.
    """

    return DEFAULT_SETTINGS_REGISTRY.snapshot()


def reset_settings() -> bool:
    """
    Reset the default settings registry.
    """

    return DEFAULT_SETTINGS_REGISTRY.reset()
    