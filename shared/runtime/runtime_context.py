"""
============================================================
Nexa Provider Platform
File: shared/runtime/runtime_context.py
Layer: Shared Runtime Foundation
Milestone: NPP-M001 — Core Foundation
Engine: Runtime Engine
============================================================

Purpose
-------
Represents one active Nexa Provider Platform runtime session.

The runtime context records:

- which configuration is active;
- when the platform started;
- the unique identity of the current runtime;
- the current runtime state;
- whether startup completed successfully;
- when shutdown occurred.

Important
---------
This module does not load configuration itself.

The future bootstrap engine will:

1. load RuntimeConfig;
2. create RuntimeContext;
3. start the remaining platform engines;
4. mark the runtime as ready.
============================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from .runtime_config import RuntimeConfig


class RuntimeState(str, Enum):
    """
    Lifecycle states supported by one platform runtime.
    """

    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    DEGRADED = "degraded"
    STOPPING = "stopping"
    STOPPED = "stopped"
    FAILED = "failed"


class RuntimeContextError(RuntimeError):
    """
    Raised when an invalid runtime state transition is attempted.
    """


def utc_now() -> datetime:
    """
    Return the current timezone-aware UTC timestamp.
    """

    return datetime.now(timezone.utc)


@dataclass(slots=True)
class RuntimeContext:
    """
    Holds the live state of one Nexa Provider Platform session.

    Unlike RuntimeConfig, this object is intentionally mutable
    because the runtime state changes while the platform starts,
    operates, degrades, fails, or shuts down.
    """

    config: RuntimeConfig

    runtime_id: UUID = field(default_factory=uuid4)
    state: RuntimeState = RuntimeState.CREATED

    created_at: datetime = field(default_factory=utc_now)
    initialization_started_at: datetime | None = None
    ready_at: datetime | None = None
    shutdown_started_at: datetime | None = None
    stopped_at: datetime | None = None
    failed_at: datetime | None = None

    failure_reason: str | None = None
    degradation_reason: str | None = None

    initialized_components: list[str] = field(default_factory=list)

    @property
    def runtime_id_string(self) -> str:
        """
        Return the runtime identity as a string.
        """

        return str(self.runtime_id)

    @property
    def is_ready(self) -> bool:
        """
        Return True when the platform is ready for requests.
        """

        return self.state == RuntimeState.READY

    @property
    def is_active(self) -> bool:
        """
        Return True while the runtime is still operating.
        """

        return self.state in {
            RuntimeState.INITIALIZING,
            RuntimeState.READY,
            RuntimeState.DEGRADED,
        }

    @property
    def is_terminal(self) -> bool:
        """
        Return True when the runtime cannot continue operating.
        """

        return self.state in {
            RuntimeState.STOPPED,
            RuntimeState.FAILED,
        }

    @property
    def uptime_seconds(self) -> float:
        """
        Return the runtime duration in seconds.

        For an active runtime, the current UTC time is used.
        For a stopped or failed runtime, the final timestamp is used.
        """

        end_time = (
            self.stopped_at
            or self.failed_at
            or utc_now()
        )

        return max(
            0.0,
            (end_time - self.created_at).total_seconds(),
        )

    def begin_initialization(self) -> None:
        """
        Move the runtime from CREATED to INITIALIZING.
        """

        self._require_state(
            RuntimeState.CREATED,
            operation="begin initialization",
        )

        self.state = RuntimeState.INITIALIZING
        self.initialization_started_at = utc_now()

    def register_component(self, component_name: str) -> None:
        """
        Record a successfully initialized platform component.

        Examples
        --------
        runtime.register_component("runtime")
        runtime.register_component("logging")
        runtime.register_component("events")
        """

        if self.state != RuntimeState.INITIALIZING:
            raise RuntimeContextError(
                "Components can only be registered while the "
                "runtime is initializing."
            )

        normalized_name = component_name.strip().lower()

        if not normalized_name:
            raise RuntimeContextError(
                "Component name cannot be empty."
            )

        if normalized_name not in self.initialized_components:
            self.initialized_components.append(normalized_name)

    def mark_ready(self) -> None:
        """
        Mark initialization as complete.

        After this transition, provider requests may be accepted.
        """

        self._require_state(
            RuntimeState.INITIALIZING,
            operation="mark runtime ready",
        )

        self.state = RuntimeState.READY
        self.ready_at = utc_now()
        self.degradation_reason = None

    def mark_degraded(self, reason: str) -> None:
        """
        Mark the runtime as operational but impaired.

        A degraded runtime may continue serving limited operations.
        """

        if self.state not in {
            RuntimeState.READY,
            RuntimeState.DEGRADED,
        }:
            raise RuntimeContextError(
                "Only a ready or already degraded runtime can be "
                "marked as degraded."
            )

        normalized_reason = reason.strip()

        if not normalized_reason:
            raise RuntimeContextError(
                "A degradation reason is required."
            )

        self.state = RuntimeState.DEGRADED
        self.degradation_reason = normalized_reason

    def restore_ready(self) -> None:
        """
        Restore a degraded runtime to the READY state.
        """

        self._require_state(
            RuntimeState.DEGRADED,
            operation="restore runtime readiness",
        )

        self.state = RuntimeState.READY
        self.degradation_reason = None

    def begin_shutdown(self) -> None:
        """
        Start graceful shutdown.
        """

        if self.state not in {
            RuntimeState.INITIALIZING,
            RuntimeState.READY,
            RuntimeState.DEGRADED,
        }:
            raise RuntimeContextError(
                f"Cannot begin shutdown while runtime is "
                f"{self.state.value!r}."
            )

        self.state = RuntimeState.STOPPING
        self.shutdown_started_at = utc_now()

    def mark_stopped(self) -> None:
        """
        Mark graceful shutdown as complete.
        """

        self._require_state(
            RuntimeState.STOPPING,
            operation="mark runtime stopped",
        )

        self.state = RuntimeState.STOPPED
        self.stopped_at = utc_now()

    def mark_failed(self, reason: str) -> None:
        """
        Mark the runtime as failed.

        Failure may occur during initialization or normal operation.
        Once failed, the runtime is terminal and cannot resume.
        """

        if self.is_terminal:
            raise RuntimeContextError(
                f"Cannot mark runtime as failed because it is "
                f"already {self.state.value!r}."
            )

        normalized_reason = reason.strip()

        if not normalized_reason:
            raise RuntimeContextError(
                "A runtime failure reason is required."
            )

        self.state = RuntimeState.FAILED
        self.failure_reason = normalized_reason
        self.failed_at = utc_now()

    def require_ready(self) -> None:
        """
        Ensure the runtime is ready before handling a request.

        Provider engines will call this before accepting work.
        """

        if self.state != RuntimeState.READY:
            raise RuntimeContextError(
                "The Nexa Provider Platform is not ready. "
                f"Current runtime state: {self.state.value}."
            )

    def to_safe_dict(self) -> dict[str, Any]:
        """
        Return a serializable runtime summary.

        This representation contains no secrets and may be used
        in logs, diagnostics, or a future administrator dashboard.
        """

        return {
            "runtime_id": self.runtime_id_string,
            "platform_name": self.config.platform_name,
            "platform_version": self.config.platform_version,
            "environment": self.config.environment.value,
            "country_profile": self.config.country_profile,
            "simulation_enabled": self.config.simulation_enabled,
            "state": self.state.value,
            "created_at": self._format_timestamp(self.created_at),
            "initialization_started_at": self._format_timestamp(
                self.initialization_started_at
            ),
            "ready_at": self._format_timestamp(self.ready_at),
            "shutdown_started_at": self._format_timestamp(
                self.shutdown_started_at
            ),
            "stopped_at": self._format_timestamp(self.stopped_at),
            "failed_at": self._format_timestamp(self.failed_at),
            "failure_reason": self.failure_reason,
            "degradation_reason": self.degradation_reason,
            "initialized_components": list(
                self.initialized_components
            ),
            "uptime_seconds": round(self.uptime_seconds, 3),
        }

    def status_summary(self) -> str:
        """
        Produce a human-readable runtime status summary.
        """

        components = (
            ", ".join(self.initialized_components)
            if self.initialized_components
            else "None"
        )

        lines = [
            "=" * 48,
            self.config.platform_name,
            f"Runtime ID: {self.runtime_id_string}",
            f"State: {self.state.value.title()}",
            f"Environment: {self.config.environment.value.title()}",
            f"Country profile: {self.config.country_profile}",
            f"Simulation: "
            f"{'Enabled' if self.config.simulation_enabled else 'Disabled'}",
            f"Initialized components: {components}",
            f"Uptime: {self.uptime_seconds:.2f} seconds",
        ]

        if self.degradation_reason:
            lines.append(
                f"Degradation reason: {self.degradation_reason}"
            )

        if self.failure_reason:
            lines.append(
                f"Failure reason: {self.failure_reason}"
            )

        lines.append("=" * 48)

        return "\n".join(lines)

    def _require_state(
        self,
        expected_state: RuntimeState,
        operation: str,
    ) -> None:
        """
        Require one exact state before performing an operation.
        """

        if self.state != expected_state:
            raise RuntimeContextError(
                f"Cannot {operation} while runtime is "
                f"{self.state.value!r}. Expected state: "
                f"{expected_state.value!r}."
            )

    @staticmethod
    def _format_timestamp(
        value: datetime | None,
    ) -> str | None:
        """
        Convert a datetime into an ISO-8601 string.
        """

        return value.isoformat() if value is not None else None


def create_runtime_context(
    config: RuntimeConfig,
) -> RuntimeContext:
    """
    Public factory for creating a new runtime context.

    The function validates the supplied configuration but does not
    begin initialization automatically.
    """

    config.validate()

    return RuntimeContext(config=config)