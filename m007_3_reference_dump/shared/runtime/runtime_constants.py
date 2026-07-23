"""
============================================================
Nexa Provider Platform
File: shared/runtime/runtime_constants.py
Layer: Shared Runtime Foundation
Milestone: NPP-M001 — Core Foundation
Engine: Runtime Engine
============================================================

Purpose
-------
Defines stable constants shared across the Runtime Engine.

This module centralizes:

- platform identity defaults;
- supported environment-variable names;
- runtime component names;
- local and remote storage backend names;
- lifecycle-state groups;
- configuration defaults;
- validation limits.

Important
---------
This module contains constants only.

It must not:

- load environment variables;
- create runtime configuration;
- mutate runtime state;
- start or stop platform components;
- connect to storage;
- import RuntimeConfig, RuntimeContext, or RuntimeManager.

Keeping this module dependency-free prevents circular imports and
allows every runtime module to use the same stable vocabulary.
============================================================
"""

from __future__ import annotations

from pathlib import Path
from typing import Final


# ============================================================
# Platform identity
# ============================================================

DEFAULT_PLATFORM_NAME: Final[str] = "Nexa Provider Platform"
DEFAULT_PLATFORM_VERSION: Final[str] = "0.1.0-alpha"


# ============================================================
# Configuration defaults
# ============================================================

DEFAULT_ENVIRONMENT: Final[str] = "development"
DEFAULT_STORAGE_BACKEND: Final[str] = "json"
DEFAULT_DEVELOPMENT_LOG_LEVEL: Final[str] = "debug"
DEFAULT_NON_DEVELOPMENT_LOG_LEVEL: Final[str] = "info"

DEFAULT_SIMULATION_ENABLED: Final[bool] = True
DEFAULT_AUDIT_ENABLED: Final[bool] = True
DEFAULT_LOGGING_ENABLED: Final[bool] = True
DEFAULT_STRICT_VALIDATION: Final[bool] = True

DEFAULT_COUNTRY_CODE: Final[str] = "SIM"
DEFAULT_COUNTRY_PROFILE: Final[str] = "nexa-simulated-country"
DEFAULT_DATA_DIRECTORY: Final[Path] = Path("storage/data")


# ============================================================
# Environment-variable names
# ============================================================

ENV_PLATFORM_NAME: Final[str] = "NPP_PLATFORM_NAME"
ENV_PLATFORM_VERSION: Final[str] = "NPP_PLATFORM_VERSION"
ENV_RUNTIME_ENVIRONMENT: Final[str] = "NPP_ENVIRONMENT"
ENV_STORAGE_BACKEND: Final[str] = "NPP_STORAGE_BACKEND"
ENV_LOG_LEVEL: Final[str] = "NPP_LOG_LEVEL"
ENV_SIMULATION_ENABLED: Final[str] = "NPP_SIMULATION_ENABLED"
ENV_AUDIT_ENABLED: Final[str] = "NPP_AUDIT_ENABLED"
ENV_LOGGING_ENABLED: Final[str] = "NPP_LOGGING_ENABLED"
ENV_STRICT_VALIDATION: Final[str] = "NPP_STRICT_VALIDATION"
ENV_COUNTRY_CODE: Final[str] = "NPP_COUNTRY_CODE"
ENV_COUNTRY_PROFILE: Final[str] = "NPP_COUNTRY_PROFILE"
ENV_DATA_DIRECTORY: Final[str] = "NPP_DATA_DIRECTORY"

RUNTIME_ENVIRONMENT_VARIABLES: Final[tuple[str, ...]] = (
    ENV_PLATFORM_NAME,
    ENV_PLATFORM_VERSION,
    ENV_RUNTIME_ENVIRONMENT,
    ENV_STORAGE_BACKEND,
    ENV_LOG_LEVEL,
    ENV_SIMULATION_ENABLED,
    ENV_AUDIT_ENABLED,
    ENV_LOGGING_ENABLED,
    ENV_STRICT_VALIDATION,
    ENV_COUNTRY_CODE,
    ENV_COUNTRY_PROFILE,
    ENV_DATA_DIRECTORY,
)


# ============================================================
# Boolean parsing vocabulary
# ============================================================

TRUE_TEXT_VALUES: Final[frozenset[str]] = frozenset(
    {
        "true",
        "1",
        "yes",
        "on",
        "enabled",
    }
)

FALSE_TEXT_VALUES: Final[frozenset[str]] = frozenset(
    {
        "false",
        "0",
        "no",
        "off",
        "disabled",
    }
)


# ============================================================
# Runtime environments
# ============================================================

ENVIRONMENT_DEVELOPMENT: Final[str] = "development"
ENVIRONMENT_TESTING: Final[str] = "testing"
ENVIRONMENT_STAGING: Final[str] = "staging"
ENVIRONMENT_PRODUCTION: Final[str] = "production"

SUPPORTED_RUNTIME_ENVIRONMENTS: Final[tuple[str, ...]] = (
    ENVIRONMENT_DEVELOPMENT,
    ENVIRONMENT_TESTING,
    ENVIRONMENT_STAGING,
    ENVIRONMENT_PRODUCTION,
)

DEBUG_LOG_ENVIRONMENTS: Final[frozenset[str]] = frozenset(
    {
        ENVIRONMENT_DEVELOPMENT,
        ENVIRONMENT_TESTING,
    }
)


# ============================================================
# Storage backends
# ============================================================

STORAGE_BACKEND_MEMORY: Final[str] = "memory"
STORAGE_BACKEND_JSON: Final[str] = "json"
STORAGE_BACKEND_JSONL: Final[str] = "jsonl"
STORAGE_BACKEND_CSV: Final[str] = "csv"
STORAGE_BACKEND_SUPABASE: Final[str] = "supabase"
STORAGE_BACKEND_POSTGRESQL: Final[str] = "postgresql"

LOCAL_STORAGE_BACKENDS: Final[frozenset[str]] = frozenset(
    {
        STORAGE_BACKEND_MEMORY,
        STORAGE_BACKEND_JSON,
        STORAGE_BACKEND_JSONL,
        STORAGE_BACKEND_CSV,
    }
)

REMOTE_STORAGE_BACKENDS: Final[frozenset[str]] = frozenset(
    {
        STORAGE_BACKEND_SUPABASE,
        STORAGE_BACKEND_POSTGRESQL,
    }
)

SUPPORTED_STORAGE_BACKENDS: Final[tuple[str, ...]] = (
    STORAGE_BACKEND_MEMORY,
    STORAGE_BACKEND_JSON,
    STORAGE_BACKEND_JSONL,
    STORAGE_BACKEND_CSV,
    STORAGE_BACKEND_SUPABASE,
    STORAGE_BACKEND_POSTGRESQL,
)


# ============================================================
# Log levels
# ============================================================

LOG_LEVEL_DEBUG: Final[str] = "debug"
LOG_LEVEL_INFO: Final[str] = "info"
LOG_LEVEL_WARNING: Final[str] = "warning"
LOG_LEVEL_ERROR: Final[str] = "error"
LOG_LEVEL_CRITICAL: Final[str] = "critical"

SUPPORTED_LOG_LEVELS: Final[tuple[str, ...]] = (
    LOG_LEVEL_DEBUG,
    LOG_LEVEL_INFO,
    LOG_LEVEL_WARNING,
    LOG_LEVEL_ERROR,
    LOG_LEVEL_CRITICAL,
)


# ============================================================
# Runtime lifecycle states
# ============================================================

RUNTIME_STATE_CREATED: Final[str] = "created"
RUNTIME_STATE_INITIALIZING: Final[str] = "initializing"
RUNTIME_STATE_READY: Final[str] = "ready"
RUNTIME_STATE_DEGRADED: Final[str] = "degraded"
RUNTIME_STATE_STOPPING: Final[str] = "stopping"
RUNTIME_STATE_STOPPED: Final[str] = "stopped"
RUNTIME_STATE_FAILED: Final[str] = "failed"

SUPPORTED_RUNTIME_STATES: Final[tuple[str, ...]] = (
    RUNTIME_STATE_CREATED,
    RUNTIME_STATE_INITIALIZING,
    RUNTIME_STATE_READY,
    RUNTIME_STATE_DEGRADED,
    RUNTIME_STATE_STOPPING,
    RUNTIME_STATE_STOPPED,
    RUNTIME_STATE_FAILED,
)

ACTIVE_RUNTIME_STATES: Final[frozenset[str]] = frozenset(
    {
        RUNTIME_STATE_INITIALIZING,
        RUNTIME_STATE_READY,
        RUNTIME_STATE_DEGRADED,
    }
)

TERMINAL_RUNTIME_STATES: Final[frozenset[str]] = frozenset(
    {
        RUNTIME_STATE_STOPPED,
        RUNTIME_STATE_FAILED,
    }
)

SHUTDOWN_ALLOWED_STATES: Final[frozenset[str]] = frozenset(
    {
        RUNTIME_STATE_INITIALIZING,
        RUNTIME_STATE_READY,
        RUNTIME_STATE_DEGRADED,
    }
)

DEGRADATION_ALLOWED_STATES: Final[frozenset[str]] = frozenset(
    {
        RUNTIME_STATE_READY,
        RUNTIME_STATE_DEGRADED,
    }
)


# ============================================================
# Runtime component names
# ============================================================

COMPONENT_RUNTIME: Final[str] = "runtime"
COMPONENT_CONFIGURATION: Final[str] = "configuration"
COMPONENT_LOGGING: Final[str] = "logging"
COMPONENT_STORAGE: Final[str] = "storage"
COMPONENT_REPOSITORIES: Final[str] = "repositories"
COMPONENT_VALIDATION: Final[str] = "validation"
COMPONENT_EVENTS: Final[str] = "events"
COMPONENT_AUDIT: Final[str] = "audit"
COMPONENT_SECURITY: Final[str] = "security"
COMPONENT_SERVICES: Final[str] = "services"
COMPONENT_CLI: Final[str] = "cli"
COMPONENT_API: Final[str] = "api"
COMPONENT_SYNC: Final[str] = "sync"

STANDARD_RUNTIME_COMPONENTS: Final[tuple[str, ...]] = (
    COMPONENT_RUNTIME,
    COMPONENT_CONFIGURATION,
    COMPONENT_LOGGING,
    COMPONENT_STORAGE,
    COMPONENT_REPOSITORIES,
    COMPONENT_VALIDATION,
    COMPONENT_EVENTS,
    COMPONENT_AUDIT,
    COMPONENT_SECURITY,
    COMPONENT_SERVICES,
    COMPONENT_CLI,
    COMPONENT_API,
    COMPONENT_SYNC,
)


# ============================================================
# Validation boundaries
# ============================================================

MAX_COUNTRY_CODE_LENGTH: Final[int] = 8
MAX_COMPONENT_NAME_LENGTH: Final[int] = 128
MAX_RUNTIME_REASON_LENGTH: Final[int] = 2_000


# ============================================================
# Display formatting
# ============================================================

RUNTIME_SUMMARY_WIDTH: Final[int] = 48
RUNTIME_NOT_STARTED_STATE: Final[str] = "not_started"


__all__ = [
    "ACTIVE_RUNTIME_STATES",
    "COMPONENT_API",
    "COMPONENT_AUDIT",
    "COMPONENT_CLI",
    "COMPONENT_CONFIGURATION",
    "COMPONENT_EVENTS",
    "COMPONENT_LOGGING",
    "COMPONENT_REPOSITORIES",
    "COMPONENT_RUNTIME",
    "COMPONENT_SECURITY",
    "COMPONENT_SERVICES",
    "COMPONENT_STORAGE",
    "COMPONENT_SYNC",
    "COMPONENT_VALIDATION",
    "DEBUG_LOG_ENVIRONMENTS",
    "DEFAULT_AUDIT_ENABLED",
    "DEFAULT_COUNTRY_CODE",
    "DEFAULT_COUNTRY_PROFILE",
    "DEFAULT_DATA_DIRECTORY",
    "DEFAULT_DEVELOPMENT_LOG_LEVEL",
    "DEFAULT_ENVIRONMENT",
    "DEFAULT_LOGGING_ENABLED",
    "DEFAULT_NON_DEVELOPMENT_LOG_LEVEL",
    "DEFAULT_PLATFORM_NAME",
    "DEFAULT_PLATFORM_VERSION",
    "DEFAULT_SIMULATION_ENABLED",
    "DEFAULT_STORAGE_BACKEND",
    "DEFAULT_STRICT_VALIDATION",
    "DEGRADATION_ALLOWED_STATES",
    "ENV_AUDIT_ENABLED",
    "ENV_COUNTRY_CODE",
    "ENV_COUNTRY_PROFILE",
    "ENV_DATA_DIRECTORY",
    "ENV_LOGGING_ENABLED",
    "ENV_LOG_LEVEL",
    "ENV_PLATFORM_NAME",
    "ENV_PLATFORM_VERSION",
    "ENV_RUNTIME_ENVIRONMENT",
    "ENV_SIMULATION_ENABLED",
    "ENV_STORAGE_BACKEND",
    "ENV_STRICT_VALIDATION",
    "ENVIRONMENT_DEVELOPMENT",
    "ENVIRONMENT_PRODUCTION",
    "ENVIRONMENT_STAGING",
    "ENVIRONMENT_TESTING",
    "FALSE_TEXT_VALUES",
    "LOCAL_STORAGE_BACKENDS",
    "LOG_LEVEL_CRITICAL",
    "LOG_LEVEL_DEBUG",
    "LOG_LEVEL_ERROR",
    "LOG_LEVEL_INFO",
    "LOG_LEVEL_WARNING",
    "MAX_COMPONENT_NAME_LENGTH",
    "MAX_COUNTRY_CODE_LENGTH",
    "MAX_RUNTIME_REASON_LENGTH",
    "REMOTE_STORAGE_BACKENDS",
    "RUNTIME_ENVIRONMENT_VARIABLES",
    "RUNTIME_NOT_STARTED_STATE",
    "RUNTIME_STATE_CREATED",
    "RUNTIME_STATE_DEGRADED",
    "RUNTIME_STATE_FAILED",
    "RUNTIME_STATE_INITIALIZING",
    "RUNTIME_STATE_READY",
    "RUNTIME_STATE_STOPPED",
    "RUNTIME_STATE_STOPPING",
    "RUNTIME_SUMMARY_WIDTH",
    "SHUTDOWN_ALLOWED_STATES",
    "STANDARD_RUNTIME_COMPONENTS",
    "STORAGE_BACKEND_CSV",
    "STORAGE_BACKEND_JSON",
    "STORAGE_BACKEND_JSONL",
    "STORAGE_BACKEND_MEMORY",
    "STORAGE_BACKEND_POSTGRESQL",
    "STORAGE_BACKEND_SUPABASE",
    "SUPPORTED_LOG_LEVELS",
    "SUPPORTED_RUNTIME_ENVIRONMENTS",
    "SUPPORTED_RUNTIME_STATES",
    "SUPPORTED_STORAGE_BACKENDS",
    "TERMINAL_RUNTIME_STATES",
    "TRUE_TEXT_VALUES",
]
