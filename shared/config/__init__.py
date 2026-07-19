"""
============================================================
Nexa Provider Platform
File: shared/config/__init__.py
Layer: Shared Configuration Foundation
Milestone: NPP-M003 — Configuration Engine
============================================================

Purpose
-------
Defines the public interface of the Nexa Provider Platform
Configuration Engine.

This package combines:

- Environment definitions
- Immutable configuration schema
- Configuration validation
- Configuration loading
- Active settings management

Platform modules should normally import configuration components
from shared.config instead of importing individual internal files.

Recommended Usage
-----------------
Initialize platform settings:

from shared.config import initialize_settings

initialize_settings(
    configuration_file="./configs/platform.json",
)

Access active settings:

from shared.config import settings

print(settings.environment)
print(settings.application_name)
print(settings.storage_directory)

Load configuration without installing it:

from shared.config import load_configuration

configuration = load_configuration(
    configuration_file="./configs/platform.json",
)

Validate an existing ConfigurationSchema:

from shared.config import validate_configuration

result = validate_configuration(configuration)

Package Responsibilities
------------------------
The Configuration Engine is responsible for:

- Defining supported deployment environments
- Defining the immutable platform configuration schema
- Loading configuration from supported sources
- Applying configuration precedence
- Normalizing configuration values
- Validating configuration rules
- Enforcing environment-specific policy
- Installing active process-wide settings
- Providing read-only configuration access

The Configuration Engine is not responsible for:

- Creating storage directories
- Starting runtime services
- Starting logging services
- Writing audit records
- Persisting configuration changes
- Managing application secrets
- Modifying operating-system environment variables

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
============================================================
"""

from __future__ import annotations


"""
============================================================
SECTION 1 — Environment Public Interface
============================================================

This section exports the supported deployment-environment model.

Environment
    Enumeration of development, testing, staging, and production.

EnvironmentError
    Raised when an unsupported environment value is supplied.

DEFAULT_ENVIRONMENT
    Default deployment environment used by ConfigurationSchema.
============================================================
"""

from .environment import (
    DEFAULT_ENVIRONMENT,
    Environment,
    EnvironmentError,
)


"""
============================================================
SECTION 2 — Configuration Schema Public Interface
============================================================

This section exports the immutable configuration data model.

ConfigurationSchema
    Frozen configuration object consumed by platform modules.

ConfigurationSchemaError
    Reserved schema-level exception for invalid schema creation.
============================================================
"""

from .config_schema import (
    ConfigurationSchema,
    ConfigurationSchemaError,
)


"""
============================================================
SECTION 3 — Configuration Validator Public Interface
============================================================

This section exports configuration validation components.

ConfigurationValidator
    Main validation engine.

ConfigurationValidationResult
    Immutable result containing validation findings.

ConfigurationValidationMessage
    One structured validation finding.

ConfigurationValidationError
    Raised by fail-fast validation.

ValidationSeverity
    Error, warning, or information severity.

DEFAULT_CONFIGURATION_VALIDATOR
    Shared default validator instance.

validate_configuration()
    Validate and return a structured result.

validate_configuration_or_raise()
    Validate and raise when invalid.

is_configuration_valid()
    Return a Boolean validation result.
============================================================
"""

from .config_validator import (
    DEFAULT_CONFIGURATION_VALIDATOR,
    ConfigurationValidationError,
    ConfigurationValidationMessage,
    ConfigurationValidationResult,
    ConfigurationValidator,
    ValidationSeverity,
    is_configuration_valid,
    validate_configuration,
    validate_configuration_or_raise,
)


"""
============================================================
SECTION 4 — Configuration Loader Public Interface
============================================================

This section exports configuration loading components.

ConfigurationLoader
    Main configuration loading engine.

ConfigLoader
    Concise compatibility alias for ConfigurationLoader.

ConfigurationLoadResult
    Structured result containing configuration, validation, and
    source information.

ConfigurationSource
    Identifies where each final field value originated.

ConfigurationLoadError
    Base configuration loading exception.

ConfigurationFileError
    Raised for missing, unreadable, or invalid JSON files.

ConfigurationValueError
    Raised when a raw value cannot be normalized.

UnknownConfigurationFieldError
    Raised when unsupported fields are supplied.

DEFAULT_CONFIGURATION_LOADER
    Shared default loader instance.

load_configuration()
    Load and return ConfigurationSchema.

load_configuration_with_result()
    Load and return ConfigurationLoadResult.

load_configuration_file()
    Load one JSON configuration file.

load_default_configuration()
    Load ConfigurationSchema defaults.
============================================================
"""

from .config_loader import (
    DEFAULT_CONFIGURATION_LOADER,
    ConfigLoader,
    ConfigurationFileError,
    ConfigurationLoadError,
    ConfigurationLoadResult,
    ConfigurationLoader,
    ConfigurationSource,
    ConfigurationValueError,
    UnknownConfigurationFieldError,
    load_configuration,
    load_configuration_file,
    load_configuration_with_result,
    load_default_configuration,
)


"""
============================================================
SECTION 5 — Settings Public Interface
============================================================

This section exports active-settings management components.

SettingsRegistry
    Thread-safe owner of one active configuration.

SettingsProxy
    Read-only attribute-style view of active settings.

SettingsMapping
    Read-only mapping-style view of active settings.

SettingsSnapshot
    Immutable snapshot of registry state.

SettingsError
    Base settings exception.

SettingsNotInitializedError
    Raised when settings are requested before initialization.

SettingsAlreadyInitializedError
    Raised when settings are initialized twice without permission.

SettingsReplacementError
    Raised when configuration replacement is rejected.

UnknownSettingError
    Raised when an unsupported setting is requested.

SettingsStateError
    Raised when settings state becomes inconsistent.

DEFAULT_SETTINGS_REGISTRY
    Process-wide default settings registry.

settings
    Attribute-style process-wide settings proxy.

settings_mapping
    Mapping-style process-wide settings view.
============================================================
"""

from .settings import (
    DEFAULT_SETTINGS_NAME,
    DEFAULT_SETTINGS_REGISTRY,
    FIRST_SETTINGS_GENERATION,
    UNINITIALIZED_GENERATION,
    SettingsAlreadyInitializedError,
    SettingsError,
    SettingsMapping,
    SettingsNotInitializedError,
    SettingsProxy,
    SettingsRegistry,
    SettingsReplacementError,
    SettingsSnapshot,
    SettingsStateError,
    UnknownSettingError,
    get_setting,
    get_setting_source,
    get_settings,
    get_settings_generation,
    get_settings_result,
    get_settings_snapshot,
    get_settings_validation,
    initialize_settings,
    install_settings,
    is_settings_initialized,
    require_setting,
    reset_settings,
    settings,
    settings_mapping,
)


"""
============================================================
SECTION 6 — Configuration Engine Metadata
============================================================

These values identify the Configuration Engine milestone and
package version.

They are package metadata only.

They do not replace ConfigurationSchema.application_version,
which identifies the running application version.
============================================================
"""

CONFIGURATION_ENGINE_NAME = "Nexa Provider Platform Configuration Engine"

CONFIGURATION_ENGINE_MILESTONE = "NPP-M003"

CONFIGURATION_ENGINE_VERSION = "0.1.0"


"""
============================================================
SECTION 7 — Public Export Definition
============================================================

__all__ defines the supported public interface of shared.config.

Names omitted from __all__ should be treated as internal package
implementation details.

This provides:

- Predictable wildcard imports
- Clear editor auto-completion
- Stable package documentation
- Controlled public API evolution
============================================================
"""

__all__ = (
    # --------------------------------------------------------
    # Configuration Engine Metadata
    # --------------------------------------------------------
    "CONFIGURATION_ENGINE_NAME",
    "CONFIGURATION_ENGINE_MILESTONE",
    "CONFIGURATION_ENGINE_VERSION",

    # --------------------------------------------------------
    # Environment
    # --------------------------------------------------------
    "Environment",
    "EnvironmentError",
    "DEFAULT_ENVIRONMENT",

    # --------------------------------------------------------
    # Configuration Schema
    # --------------------------------------------------------
    "ConfigurationSchema",
    "ConfigurationSchemaError",

    # --------------------------------------------------------
    # Configuration Validation
    # --------------------------------------------------------
    "ValidationSeverity",
    "ConfigurationValidationMessage",
    "ConfigurationValidationResult",
    "ConfigurationValidationError",
    "ConfigurationValidator",
    "DEFAULT_CONFIGURATION_VALIDATOR",
    "validate_configuration",
    "validate_configuration_or_raise",
    "is_configuration_valid",

    # --------------------------------------------------------
    # Configuration Loading
    # --------------------------------------------------------
    "ConfigurationSource",
    "ConfigurationLoadError",
    "ConfigurationFileError",
    "ConfigurationValueError",
    "UnknownConfigurationFieldError",
    "ConfigurationLoadResult",
    "ConfigurationLoader",
    "ConfigLoader",
    "DEFAULT_CONFIGURATION_LOADER",
    "load_configuration",
    "load_configuration_with_result",
    "load_configuration_file",
    "load_default_configuration",

    # --------------------------------------------------------
    # Settings Exceptions
    # --------------------------------------------------------
    "SettingsError",
    "SettingsNotInitializedError",
    "SettingsAlreadyInitializedError",
    "SettingsReplacementError",
    "UnknownSettingError",
    "SettingsStateError",

    # --------------------------------------------------------
    # Settings State Models
    # --------------------------------------------------------
    "SettingsSnapshot",
    "SettingsRegistry",
    "SettingsProxy",
    "SettingsMapping",

    # --------------------------------------------------------
    # Settings Constants and Default Objects
    # --------------------------------------------------------
    "DEFAULT_SETTINGS_NAME",
    "UNINITIALIZED_GENERATION",
    "FIRST_SETTINGS_GENERATION",
    "DEFAULT_SETTINGS_REGISTRY",
    "settings",
    "settings_mapping",

    # --------------------------------------------------------
    # Settings Initialization and Installation
    # --------------------------------------------------------
    "initialize_settings",
    "install_settings",

    # --------------------------------------------------------
    # Settings Access
    # --------------------------------------------------------
    "get_settings",
    "get_settings_result",
    "get_settings_validation",
    "get_setting",
    "require_setting",
    "get_setting_source",

    # --------------------------------------------------------
    # Settings State
    # --------------------------------------------------------
    "is_settings_initialized",
    "get_settings_generation",
    "get_settings_snapshot",
    "reset_settings",
)
