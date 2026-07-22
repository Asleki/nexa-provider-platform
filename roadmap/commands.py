"""
Command-dispatch layer for the Nexa Provider Platform roadmap package.

The module provides an immutable command context, command results, a registry,
built-in read-only roadmap commands, text/JSON formatting, command parsing,
and a small CLI-compatible entry point. Commands delegate to the package's
query, progress, dependency, validation, verification, and generation modules.
"""

from __future__ import annotations

import json
import shlex
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Mapping, Sequence

from .dependencies import dependency_summary
from .generator import generate_artifact, write_artifact
from .models import Milestone, RoadmapMetadata, RoadmapSnapshot
from .progress import summarize_progress
from .queries import (
    MilestoneSource,
    all_milestones,
    filter_by_status,
    get_by_number,
    search,
    sort_by_sequence,
)
from .validation import validate_roadmap
from .verification import VerificationPolicy, summarize_verification


class RoadmapCommandError(ValueError):
    """Base exception for roadmap command failures."""


class UnknownCommandError(RoadmapCommandError):
    """Raised when a command name is not registered."""


class CommandUsageError(RoadmapCommandError):
    """Raised when command arguments are invalid."""


@dataclass(frozen=True, slots=True)
class CommandContext:
    """Immutable data available to command handlers."""

    source: MilestoneSource | RoadmapSnapshot
    metadata: RoadmapMetadata | None = None

    @property
    def milestones(self) -> tuple[Milestone, ...]:
        if isinstance(self.source, RoadmapSnapshot):
            return self.source.milestones
        return all_milestones(self.source)

    @property
    def resolved_metadata(self) -> RoadmapMetadata | None:
        if isinstance(self.source, RoadmapSnapshot):
            return self.source.metadata
        return self.metadata


@dataclass(frozen=True, slots=True)
class CommandResult:
    """Immutable command execution result."""

    command: str
    success: bool
    message: str
    data: object = None
    exit_code: int = 0

    def __post_init__(self) -> None:
        if not self.command.strip():
            raise ValueError("command cannot be blank")
        if not isinstance(self.exit_code, int):
            raise TypeError("exit_code must be an integer")
        if self.success and self.exit_code != 0:
            raise ValueError("successful results must use exit_code 0")
        if not self.success and self.exit_code == 0:
            raise ValueError("failed results must use a non-zero exit_code")

    def to_mapping(self) -> dict[str, object]:
        return {
            "command": self.command,
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "exit_code": self.exit_code,
        }


CommandHandler = Callable[[CommandContext, tuple[str, ...]], CommandResult]


@dataclass(frozen=True, slots=True)
class CommandDefinition:
    """One registered command."""

    name: str
    handler: CommandHandler
    help: str
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("command name cannot be blank")
        if not callable(self.handler):
            raise TypeError("handler must be callable")
        if not self.help.strip():
            raise ValueError("help cannot be blank")


class CommandRegistry:
    """Mutable registration container with immutable public indexes."""

    def __init__(self) -> None:
        self._commands: dict[str, CommandDefinition] = {}
        self._aliases: dict[str, str] = {}

    def register(self, definition: CommandDefinition) -> None:
        name = definition.name.lower()
        if name in self._commands or name in self._aliases:
            raise RoadmapCommandError(f"Duplicate command name {name!r}")
        self._commands[name] = definition
        for alias in definition.aliases:
            key = alias.lower()
            if key in self._commands or key in self._aliases:
                raise RoadmapCommandError(f"Duplicate command alias {key!r}")
            self._aliases[key] = name

    def resolve(self, name: str) -> CommandDefinition:
        key = name.strip().lower()
        key = self._aliases.get(key, key)
        try:
            return self._commands[key]
        except KeyError as exc:
            raise UnknownCommandError(f"Unknown command {name!r}") from exc

    def definitions(self) -> tuple[CommandDefinition, ...]:
        return tuple(self._commands[name] for name in sorted(self._commands))

    def command_map(self) -> Mapping[str, CommandDefinition]:
        return MappingProxyType(dict(self._commands))


def parse_command_line(command_line: str | Sequence[str]) -> tuple[str, tuple[str, ...]]:
    """Parse a shell-like command string or argument sequence."""

    if isinstance(command_line, str):
        parts = tuple(shlex.split(command_line))
    else:
        parts = tuple(str(item) for item in command_line)
    if not parts:
        raise CommandUsageError("A command is required")
    return parts[0], parts[1:]


def _milestone_mapping(item: Milestone) -> dict[str, object]:
    return {
        "record_id": item.record_id,
        "number": item.number,
        "title": item.title,
        "parent_number": item.parent_number,
        "sequence": item.sequence,
        "depth": item.depth,
        "semantic_path": item.semantic_path,
        "status": item.status.value,
        "dependencies": list(item.dependencies),
        "priority": item.priority,
        "verification_state": item.verification_state,
        "passing_tests": item.passing_tests,
        "started_date": item.started_date,
        "completed_date": item.completed_date,
    }


def _require_no_args(command: str, args: tuple[str, ...]) -> None:
    if args:
        raise CommandUsageError(f"{command} does not accept arguments")


def command_help(context: CommandContext, args: tuple[str, ...]) -> CommandResult:
    if args:
        definition = DEFAULT_REGISTRY.resolve(args[0])
        return CommandResult(
            command="help",
            success=True,
            message=f"{definition.name}: {definition.help}",
            data={
                "name": definition.name,
                "aliases": list(definition.aliases),
                "help": definition.help,
            },
        )
    data = [
        {
            "name": item.name,
            "aliases": list(item.aliases),
            "help": item.help,
        }
        for item in DEFAULT_REGISTRY.definitions()
    ]
    return CommandResult(
        command="help",
        success=True,
        message=f"{len(data)} command(s) available",
        data=data,
    )


def command_summary(context: CommandContext, args: tuple[str, ...]) -> CommandResult:
    _require_no_args("summary", args)
    records = context.milestones
    progress = summarize_progress(records)
    metadata = context.resolved_metadata
    data = {
        "title": metadata.title if metadata else None,
        "version": metadata.version if metadata else None,
        "total": len(records),
        "roots": sum(item.is_root for item in records),
        "completed": progress.complete,
        "incomplete": progress.incomplete,
        "completion_percentage": float(progress.percentage),
    }
    return CommandResult(
        command="summary",
        success=True,
        message=(
            f"{data['completed']}/{data['total']} milestones complete "
            f"({data['completion_percentage']}%)"
        ),
        data=data,
    )


def command_list(context: CommandContext, args: tuple[str, ...]) -> CommandResult:
    status = None
    limit = None
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--status":
            index += 1
            if index >= len(args):
                raise CommandUsageError("--status requires a value")
            status = args[index]
        elif token == "--limit":
            index += 1
            if index >= len(args):
                raise CommandUsageError("--limit requires a value")
            try:
                limit = int(args[index])
            except ValueError as exc:
                raise CommandUsageError("--limit must be an integer") from exc
            if limit < 0:
                raise CommandUsageError("--limit cannot be negative")
        else:
            raise CommandUsageError(f"Unknown list option {token!r}")
        index += 1

    records = context.milestones
    if status is not None:
        records = filter_by_status(records, status)
    records = sort_by_sequence(records)
    if limit is not None:
        records = records[:limit]
    data = [_milestone_mapping(item) for item in records]
    return CommandResult(
        command="list",
        success=True,
        message=f"{len(data)} milestone(s)",
        data=data,
    )


def command_show(context: CommandContext, args: tuple[str, ...]) -> CommandResult:
    if len(args) != 1:
        raise CommandUsageError("Usage: show <milestone-number>")
    item = get_by_number(context.milestones, args[0])
    return CommandResult(
        command="show",
        success=True,
        message=f"{item.number} — {item.title}",
        data=_milestone_mapping(item),
    )


def command_search(context: CommandContext, args: tuple[str, ...]) -> CommandResult:
    if not args:
        raise CommandUsageError("Usage: search <terms>")
    query = " ".join(args)
    records = search(context.milestones, query)
    data = [_milestone_mapping(item) for item in records]
    return CommandResult(
        command="search",
        success=True,
        message=f"{len(data)} match(es) for {query!r}",
        data=data,
    )


def command_progress(context: CommandContext, args: tuple[str, ...]) -> CommandResult:
    _require_no_args("progress", args)
    result = summarize_progress(context.milestones)
    data = {
        "total": result.total,
        "completed": result.complete,
        "incomplete": result.incomplete,
        "completion_percentage": float(result.percentage),
    }
    return CommandResult(
        command="progress",
        success=True,
        message=(
            f"{result.complete}/{result.total} complete "
            f"({float(result.percentage)}%)"
        ),
        data=data,
    )


def command_dependencies(context: CommandContext, args: tuple[str, ...]) -> CommandResult:
    if len(args) != 1:
        raise CommandUsageError("Usage: dependencies <milestone-number>")
    result = dependency_summary(context.milestones, args[0])
    data = {
        "number": result.milestone.number,
        "direct_dependencies": [
            item.number for item in result.direct_dependencies
        ],
        "transitive_dependencies": [
            item.number for item in result.transitive_dependencies
        ],
        "direct_dependents": [
            item.number for item in result.direct_dependents
        ],
        "blocking_dependencies": [
            item.number for item in result.blocking_dependencies
        ],
        "ready": result.is_ready,
        "dependency_depth": len(result.transitive_dependencies),
    }
    return CommandResult(
        command="dependencies",
        success=True,
        message=f"Dependency summary for {result.milestone.number}",
        data=data,
    )


def command_validate(context: CommandContext, args: tuple[str, ...]) -> CommandResult:
    _require_no_args("validate", args)
    report = validate_roadmap(
        context.source,
        metadata=context.metadata,
    )
    data = report.to_mapping()
    return CommandResult(
        command="validate",
        success=report.is_valid,
        message=(
            f"{report.error_count} error(s), "
            f"{report.warning_count} warning(s)"
        ),
        data=data,
        exit_code=0 if report.is_valid else 2,
    )


def command_verify(context: CommandContext, args: tuple[str, ...]) -> CommandResult:
    accept_current = False
    if args == ("--accept-current",):
        accept_current = True
    elif args:
        raise CommandUsageError(
            "Usage: verify [--accept-current]"
        )
    policy = None
    if accept_current:
        states = frozenset(
            item.verification_state
            for item in context.milestones
        )
        policy = VerificationPolicy(accepted_states=states)
    summary = summarize_verification(
        context.milestones,
        policy=policy,
    )
    data = summary.to_mapping()
    return CommandResult(
        command="verify",
        success=summary.failed == 0,
        message=(
            f"{summary.passed}/{summary.total} milestone(s) verified"
        ),
        data=data,
        exit_code=0 if summary.failed == 0 else 3,
    )


def command_generate(context: CommandContext, args: tuple[str, ...]) -> CommandResult:
    if not args:
        raise CommandUsageError(
            "Usage: generate <json|markdown|python|csv|tree> [output-file]"
        )
    format_name = args[0]
    if len(args) > 2:
        raise CommandUsageError(
            "Usage: generate <format> [output-file]"
        )
    artifact = generate_artifact(
        context.source,
        format=format_name,
        metadata=context.metadata,
        name=Path(args[1]).name if len(args) == 2 else None,
    )
    output_path = None
    if len(args) == 2:
        requested = Path(args[1])
        output_path = write_artifact(
            artifact,
            requested.parent if str(requested.parent) else Path("."),
            overwrite=True,
        )
    data = {
        "name": artifact.name,
        "format": artifact.format,
        "sha256": artifact.sha256,
        "size_bytes": artifact.size_bytes,
        "record_count": artifact.record_count,
        "output_path": str(output_path) if output_path else None,
        "content": None if output_path else artifact.content,
    }
    return CommandResult(
        command="generate",
        success=True,
        message=(
            f"Generated {artifact.name} "
            f"({artifact.size_bytes} bytes)"
        ),
        data=data,
    )


def build_default_registry() -> CommandRegistry:
    registry = CommandRegistry()
    definitions = (
        CommandDefinition("help", command_help, "Show available commands.", ("-h", "--help")),
        CommandDefinition("summary", command_summary, "Show roadmap summary.", ("status",)),
        CommandDefinition("list", command_list, "List milestones; supports --status and --limit.", ("ls",)),
        CommandDefinition("show", command_show, "Show one milestone by number.", ("get",)),
        CommandDefinition("search", command_search, "Search milestone text.", ("find",)),
        CommandDefinition("progress", command_progress, "Show completion progress.", ()),
        CommandDefinition("dependencies", command_dependencies, "Show dependency information.", ("deps",)),
        CommandDefinition("validate", command_validate, "Validate the roadmap.", ("check",)),
        CommandDefinition("verify", command_verify, "Verify roadmap evidence.", ()),
        CommandDefinition("generate", command_generate, "Generate a roadmap artifact.", ("export",)),
    )
    for definition in definitions:
        registry.register(definition)
    return registry


DEFAULT_REGISTRY = build_default_registry()


def execute_command(
    context: CommandContext,
    command_line: str | Sequence[str],
    *,
    registry: CommandRegistry = DEFAULT_REGISTRY,
    catch_errors: bool = True,
) -> CommandResult:
    """Parse and execute one command."""

    try:
        name, args = parse_command_line(command_line)
        definition = registry.resolve(name)
        return definition.handler(context, args)
    except Exception as exc:
        if not catch_errors:
            raise
        command = (
            command_line.split()[0]
            if isinstance(command_line, str) and command_line.split()
            else str(command_line[0])
            if not isinstance(command_line, str) and command_line
            else "command"
        )
        return CommandResult(
            command=command,
            success=False,
            message=str(exc),
            data={"error_type": type(exc).__name__},
            exit_code=1,
        )


def format_result(
    result: CommandResult,
    *,
    output: str = "text",
    indent: int = 2,
) -> str:
    """Format a command result as text or JSON."""

    normalized = output.strip().lower()
    if normalized == "json":
        return json.dumps(
            result.to_mapping(),
            indent=indent,
            ensure_ascii=False,
            default=str,
        ) + "\n"
    if normalized != "text":
        raise CommandUsageError(
            "output must be 'text' or 'json'"
        )
    if result.data is None:
        return result.message + "\n"
    return result.message + "\n" + json.dumps(
        result.data,
        indent=indent,
        ensure_ascii=False,
        default=str,
    ) + "\n"


def main(
    argv: Sequence[str] | None = None,
    *,
    context: CommandContext | None = None,
) -> int:
    """CLI-compatible entry point.

    A context must be supplied by the embedding application because this
    module intentionally does not import a particular roadmap dataset.
    """

    if context is None:
        raise RoadmapCommandError(
            "main() requires a CommandContext"
        )
    args = tuple(argv or ("help",))
    result = execute_command(context, args)
    print(format_result(result), end="")
    return result.exit_code


__all__ = (
    "CommandContext",
    "CommandDefinition",
    "CommandHandler",
    "CommandRegistry",
    "CommandResult",
    "CommandUsageError",
    "DEFAULT_REGISTRY",
    "RoadmapCommandError",
    "UnknownCommandError",
    "build_default_registry",
    "command_dependencies",
    "command_generate",
    "command_help",
    "command_list",
    "command_progress",
    "command_search",
    "command_show",
    "command_summary",
    "command_validate",
    "command_verify",
    "execute_command",
    "format_result",
    "main",
    "parse_command_line",
)
