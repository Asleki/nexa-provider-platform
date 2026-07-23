"""
============================================================
Nexa Provider Platform
File: shared/runtime/runtime_manager.py
Layer: Shared Runtime Foundation
Milestone: NPP-M001 — Core Foundation
Engine: Runtime Engine
============================================================

Purpose
-------
Coordinates the complete lifecycle of the Nexa Provider Platform
runtime.

This manager:

- loads runtime configuration;
- creates the runtime context;
- starts initialization;
- registers successfully started components;
- marks the platform ready;
- supports degraded and failed states;
- performs graceful shutdown;
- exposes the active runtime context.

Important
---------
The Runtime Manager does not contain business logic.

It does not register citizens, create phone numbers, or perform
provider operations. Its role is only to start, supervise, and
stop the platform foundation safely.
============================================================
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .runtime_config import RuntimeConfig, load_runtime_config
from .runtime_context import (
    RuntimeContext,
    RuntimeContextError,
    RuntimeState,
    create_runtime_context,
)


class RuntimeManagerError(RuntimeError):
    """
    Raised when the Runtime Manager cannot complete an operation.
    """


ComponentInitializer = Callable[[RuntimeContext], None]
ComponentShutdownHandler = Callable[[RuntimeContext], None]


@dataclass(slots=True)
class RuntimeComponent:
    """
    Describes one component managed by the Runtime Manager.

    Examples include:

    - logging;
    - errors;
    - events;
    - audit;
    - storage;
    - population generator.

    The component name must be unique within one Runtime Manager.
    """

    name: str
    initializer: ComponentInitializer
    shutdown_handler: ComponentShutdownHandler | None = None
    required: bool = True

    def normalized_name(self) -> str:
        """
        Return the normalized component name.
        """

        normalized = self.name.strip().lower()

        if not normalized:
            raise RuntimeManagerError(
                "Runtime component name cannot be empty."
            )

        return normalized


class RuntimeManager:
    """
    Starts, supervises, and stops one NPP runtime.

    Only one active RuntimeContext may be managed by this object
    at a time.
    """

    def __init__(
        self,
        config: RuntimeConfig | None = None,
    ) -> None:
        self._config = config
        self._context: RuntimeContext | None = None

        self._components: list[RuntimeComponent] = []
        self._started_components: list[RuntimeComponent] = []

    @property
    def config(self) -> RuntimeConfig | None:
        """
        Return the configured RuntimeConfig, if loaded.
        """

        return self._config

    @property
    def context(self) -> RuntimeContext | None:
        """
        Return the current RuntimeContext, if one exists.
        """

        return self._context

    @property
    def is_started(self) -> bool:
        """
        Return True after startup has begun.
        """

        return (
            self._context is not None
            and self._context.state != RuntimeState.CREATED
        )

    @property
    def is_ready(self) -> bool:
        """
        Return True when the platform is ready for requests.
        """

        return (
            self._context is not None
            and self._context.state == RuntimeState.READY
        )

    @property
    def registered_component_names(self) -> tuple[str, ...]:
        """
        Return all registered component names.
        """

        return tuple(
            component.normalized_name()
            for component in self._components
        )

    @property
    def started_component_names(self) -> tuple[str, ...]:
        """
        Return all successfully started component names.
        """

        return tuple(
            component.normalized_name()
            for component in self._started_components
        )

    def register_component(
        self,
        name: str,
        initializer: ComponentInitializer,
        shutdown_handler: ComponentShutdownHandler | None = None,
        required: bool = True,
    ) -> None:
        """
        Register a component that should start with the platform.

        Parameters
        ----------
        name
            Unique component name.

        initializer
            Function called during startup.

            It receives the active RuntimeContext.

        shutdown_handler
            Optional function called during graceful shutdown.

        required
            When True, startup fails if initialization fails.

            When False, the runtime becomes degraded and may
            continue starting.
        """

        if self.is_started:
            raise RuntimeManagerError(
                "Components cannot be registered after runtime "
                "startup has begun."
            )

        component = RuntimeComponent(
            name=name,
            initializer=initializer,
            shutdown_handler=shutdown_handler,
            required=required,
        )

        normalized_name = component.normalized_name()

        existing_names = {
            registered.normalized_name()
            for registered in self._components
        }

        if normalized_name in existing_names:
            raise RuntimeManagerError(
                f"Runtime component {normalized_name!r} is already "
                "registered."
            )

        if not callable(initializer):
            raise RuntimeManagerError(
                f"Initializer for component {normalized_name!r} "
                "must be callable."
            )

        if (
            shutdown_handler is not None
            and not callable(shutdown_handler)
        ):
            raise RuntimeManagerError(
                f"Shutdown handler for component "
                f"{normalized_name!r} must be callable."
            )

        self._components.append(component)

    def start(
        self,
        environment_variables: dict[str, str] | None = None,
    ) -> RuntimeContext:
        """
        Start the Nexa Provider Platform runtime.

        Startup order
        -------------
        1. Load and validate configuration.
        2. Create RuntimeContext.
        3. Begin initialization.
        4. Register the runtime component.
        5. Initialize registered components in order.
        6. Mark the platform ready or degraded.
        """

        if self._context is not None:
            raise RuntimeManagerError(
                "This Runtime Manager has already created a runtime."
            )

        config = self._config or load_runtime_config(
            environment_variables
        )

        config.validate()
        config.ensure_data_directory()

        context = create_runtime_context(config)

        self._config = config
        self._context = context

        try:
            context.begin_initialization()
            context.register_component("runtime")

            degradation_reasons: list[str] = []

            for component in self._components:
                component_name = component.normalized_name()

                try:
                    component.initializer(context)

                    context.register_component(component_name)
                    self._started_components.append(component)

                except Exception as error:
                    failure_message = (
                        f"Component {component_name!r} failed during "
                        f"initialization: {error}"
                    )

                    if component.required:
                        self._rollback_started_components(context)
                        context.mark_failed(failure_message)

                        raise RuntimeManagerError(
                            failure_message
                        ) from error

                    degradation_reasons.append(failure_message)

            context.mark_ready()

            if degradation_reasons:
                context.mark_degraded(
                    " | ".join(degradation_reasons)
                )

            return context

        except RuntimeManagerError:
            raise

        except Exception as error:
            if not context.is_terminal:
                context.mark_failed(
                    f"Unexpected runtime startup failure: {error}"
                )

            raise RuntimeManagerError(
                "The Nexa Provider Platform could not start."
            ) from error

    def shutdown(self) -> RuntimeContext:
        """
        Stop the runtime gracefully.

        Components are stopped in reverse startup order.
        """

        context = self.require_context()

        if context.state == RuntimeState.STOPPED:
            return context

        if context.state == RuntimeState.FAILED:
            return context

        if context.state == RuntimeState.CREATED:
            raise RuntimeManagerError(
                "The runtime was created but initialization never "
                "started."
            )

        try:
            context.begin_shutdown()

            shutdown_errors: list[str] = []

            for component in reversed(self._started_components):
                if component.shutdown_handler is None:
                    continue

                component_name = component.normalized_name()

                try:
                    component.shutdown_handler(context)
                except Exception as error:
                    shutdown_errors.append(
                        f"{component_name}: {error}"
                    )

            if shutdown_errors:
                failure_reason = (
                    "Runtime shutdown completed with component "
                    "errors: "
                    + " | ".join(shutdown_errors)
                )

                context.mark_failed(failure_reason)

                raise RuntimeManagerError(failure_reason)

            context.mark_stopped()
            self._started_components.clear()

            return context

        except RuntimeContextError as error:
            raise RuntimeManagerError(
                f"Runtime shutdown failed: {error}"
            ) from error

    def mark_degraded(self, reason: str) -> None:
        """
        Mark the active runtime as degraded.
        """

        context = self.require_context()
        context.mark_degraded(reason)

    def restore_ready(self) -> None:
        """
        Restore a degraded runtime to the ready state.
        """

        context = self.require_context()
        context.restore_ready()

    def fail_runtime(self, reason: str) -> None:
        """
        Mark the active runtime as failed.
        """

        context = self.require_context()
        context.mark_failed(reason)

    def require_context(self) -> RuntimeContext:
        """
        Return the active RuntimeContext.

        Raises an error when startup has not created one.
        """

        if self._context is None:
            raise RuntimeManagerError(
                "No runtime context exists. Start the platform first."
            )

        return self._context

    def require_ready(self) -> RuntimeContext:
        """
        Return the active context only when it is ready.
        """

        context = self.require_context()
        context.require_ready()

        return context

    def status(self) -> dict[str, Any]:
        """
        Return the complete safe runtime status.
        """

        if self._context is None:
            return {
                "state": "not_started",
                "registered_components": list(
                    self.registered_component_names
                ),
                "started_components": [],
            }

        status = self._context.to_safe_dict()

        status["registered_components"] = list(
            self.registered_component_names
        )
        status["started_components"] = list(
            self.started_component_names
        )

        return status

    def status_summary(self) -> str:
        """
        Return a readable manager and runtime summary.
        """

        if self._context is None:
            registered = (
                ", ".join(self.registered_component_names)
                if self._components
                else "None"
            )

            return "\n".join(
                [
                    "=" * 48,
                    "Nexa Provider Platform",
                    "State: Not Started",
                    f"Registered components: {registered}",
                    "=" * 48,
                ]
            )

        return self._context.status_summary()

    def _rollback_started_components(
        self,
        context: RuntimeContext,
    ) -> None:
        """
        Attempt to shut down components after startup failure.

        Rollback errors are intentionally suppressed because the
        original startup failure remains the primary error.
        """

        for component in reversed(self._started_components):
            if component.shutdown_handler is None:
                continue

            try:
                component.shutdown_handler(context)
            except Exception:
                pass

        self._started_components.clear()


def create_runtime_manager(
    config: RuntimeConfig | None = None,
) -> RuntimeManager:
    """
    Public factory for creating a Runtime Manager.
    """

    return RuntimeManager(config=config)