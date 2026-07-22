"""
Canonical roadmap status definitions for the Nexa Provider Platform.

This module is the single source of truth for roadmap lifecycle statuses,
their display metadata, ordering, and shared status predicates.
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Final, Iterable, Mapping, TypeAlias


class RoadmapStatus(str, Enum):
    """Supported lifecycle states for a roadmap milestone."""

    COMPLETED = "COMPLETED"
    IN_PROGRESS = "IN_PROGRESS"
    TESTING = "TESTING"
    STABILIZING = "STABILIZING"
    READY = "READY"
    BLOCKED = "BLOCKED"
    PLANNED = "PLANNED"
    RELEASED = "RELEASED"
    DEPRECATED = "DEPRECATED"

    def __str__(self) -> str:
        return self.value


StatusLike: TypeAlias = RoadmapStatus | str

STATUS_ORDER: Final[tuple[RoadmapStatus, ...]] = (
    RoadmapStatus.COMPLETED,
    RoadmapStatus.RELEASED,
    RoadmapStatus.IN_PROGRESS,
    RoadmapStatus.TESTING,
    RoadmapStatus.STABILIZING,
    RoadmapStatus.READY,
    RoadmapStatus.BLOCKED,
    RoadmapStatus.PLANNED,
    RoadmapStatus.DEPRECATED,
)

_STATUS_LABELS: Final[dict[RoadmapStatus, str]] = {
    RoadmapStatus.COMPLETED: "Completed",
    RoadmapStatus.IN_PROGRESS: "In Progress",
    RoadmapStatus.TESTING: "Testing",
    RoadmapStatus.STABILIZING: "Stabilizing",
    RoadmapStatus.READY: "Ready",
    RoadmapStatus.BLOCKED: "Blocked",
    RoadmapStatus.PLANNED: "Planned",
    RoadmapStatus.RELEASED: "Released",
    RoadmapStatus.DEPRECATED: "Deprecated",
}

_STATUS_EMOJIS: Final[dict[RoadmapStatus, str]] = {
    RoadmapStatus.COMPLETED: "✅",
    RoadmapStatus.IN_PROGRESS: "🟡",
    RoadmapStatus.TESTING: "🧪",
    RoadmapStatus.STABILIZING: "🛠️",
    RoadmapStatus.READY: "➡️",
    RoadmapStatus.BLOCKED: "🚧",
    RoadmapStatus.PLANNED: "⬜",
    RoadmapStatus.RELEASED: "🚀",
    RoadmapStatus.DEPRECATED: "⚠️",
}

_STATUS_ANSI_COLORS: Final[dict[RoadmapStatus, str]] = {
    RoadmapStatus.COMPLETED: "\033[92m",
    RoadmapStatus.IN_PROGRESS: "\033[93m",
    RoadmapStatus.TESTING: "\033[95m",
    RoadmapStatus.STABILIZING: "\033[96m",
    RoadmapStatus.READY: "\033[94m",
    RoadmapStatus.BLOCKED: "\033[91m",
    RoadmapStatus.PLANNED: "\033[90m",
    RoadmapStatus.RELEASED: "\033[92m",
    RoadmapStatus.DEPRECATED: "\033[91m",
}

STATUS_LABELS: Final[Mapping[RoadmapStatus, str]] = MappingProxyType(_STATUS_LABELS)
STATUS_EMOJIS: Final[Mapping[RoadmapStatus, str]] = MappingProxyType(_STATUS_EMOJIS)
STATUS_ANSI_COLORS: Final[Mapping[RoadmapStatus, str]] = MappingProxyType(
    _STATUS_ANSI_COLORS
)

ANSI_RESET: Final[str] = "\033[0m"

COMPLETE_STATUSES: Final[frozenset[RoadmapStatus]] = frozenset(
    {RoadmapStatus.COMPLETED, RoadmapStatus.RELEASED}
)

ACTIVE_STATUSES: Final[frozenset[RoadmapStatus]] = frozenset(
    {
        RoadmapStatus.IN_PROGRESS,
        RoadmapStatus.TESTING,
        RoadmapStatus.STABILIZING,
    }
)

ACTIONABLE_STATUSES: Final[frozenset[RoadmapStatus]] = frozenset(
    {
        RoadmapStatus.READY,
        RoadmapStatus.IN_PROGRESS,
        RoadmapStatus.TESTING,
        RoadmapStatus.STABILIZING,
    }
)

OPEN_STATUSES: Final[frozenset[RoadmapStatus]] = frozenset(
    {
        RoadmapStatus.IN_PROGRESS,
        RoadmapStatus.TESTING,
        RoadmapStatus.STABILIZING,
        RoadmapStatus.READY,
        RoadmapStatus.BLOCKED,
        RoadmapStatus.PLANNED,
    }
)

TERMINAL_STATUSES: Final[frozenset[RoadmapStatus]] = frozenset(
    {
        RoadmapStatus.COMPLETED,
        RoadmapStatus.RELEASED,
        RoadmapStatus.DEPRECATED,
    }
)

ALLOWED_STATUS_VALUES: Final[tuple[str, ...]] = tuple(
    status.value for status in RoadmapStatus
)

_STATUS_ALIASES: Final[Mapping[str, RoadmapStatus]] = MappingProxyType(
    {
        "COMPLETE": RoadmapStatus.COMPLETED,
        "DONE": RoadmapStatus.COMPLETED,
        "FINISHED": RoadmapStatus.COMPLETED,
        "INPROGRESS": RoadmapStatus.IN_PROGRESS,
        "IN-PROGRESS": RoadmapStatus.IN_PROGRESS,
        "WORKING": RoadmapStatus.IN_PROGRESS,
        "UNDERTEST": RoadmapStatus.TESTING,
        "UNDER-TEST": RoadmapStatus.TESTING,
        "AVAILABLE": RoadmapStatus.READY,
        "WAITING": RoadmapStatus.PLANNED,
        "TODO": RoadmapStatus.PLANNED,
        "TO-DO": RoadmapStatus.PLANNED,
        "OBSOLETE": RoadmapStatus.DEPRECATED,
        "ARCHIVED": RoadmapStatus.DEPRECATED,
        "SHIPPED": RoadmapStatus.RELEASED,
    }
)


def _canonicalize_text(value: str) -> str:
    return value.strip().upper().replace(" ", "_")


def normalize_status(
    status: StatusLike,
    *,
    allow_aliases: bool = True,
) -> RoadmapStatus:
    """Convert a status enum or string into ``RoadmapStatus``."""

    if isinstance(status, RoadmapStatus):
        return status
    if not isinstance(status, str):
        raise TypeError(
            "status must be a RoadmapStatus or string, "
            f"received {type(status).__name__}"
        )

    canonical = _canonicalize_text(status)
    if not canonical:
        raise ValueError("status cannot be blank")

    try:
        return RoadmapStatus(canonical)
    except ValueError:
        if allow_aliases:
            compact = canonical.replace("_", "")
            for alias, target in _STATUS_ALIASES.items():
                if alias.replace("_", "") == compact:
                    return target

    allowed = ", ".join(ALLOWED_STATUS_VALUES)
    raise ValueError(
        f"Unsupported roadmap status {status!r}. Allowed values: {allowed}"
    )


def is_valid_status(
    status: object,
    *,
    allow_aliases: bool = False,
) -> bool:
    """Return whether a value is a supported roadmap status."""

    try:
        normalize_status(status, allow_aliases=allow_aliases)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return False
    return True


def get_status_label(status: StatusLike) -> str:
    return STATUS_LABELS[normalize_status(status)]


def get_status_emoji(status: StatusLike, *, enabled: bool = True) -> str:
    if not enabled:
        return ""
    return STATUS_EMOJIS[normalize_status(status)]


def get_status_color(status: StatusLike, *, enabled: bool = True) -> str:
    if not enabled:
        return ""
    return STATUS_ANSI_COLORS[normalize_status(status)]


def format_status(
    status: StatusLike,
    *,
    emoji: bool = True,
    color: bool = False,
    include_value: bool = False,
) -> str:
    """Render a status for terminal or plain-text output."""

    normalized = normalize_status(status)
    label = STATUS_LABELS[normalized]
    if include_value:
        label = f"{label} ({normalized.value})"

    icon = STATUS_EMOJIS[normalized] if emoji else ""
    text = f"{icon} {label}" if icon else label

    if color:
        return f"{STATUS_ANSI_COLORS[normalized]}{text}{ANSI_RESET}"
    return text


def status_rank(status: StatusLike) -> int:
    return STATUS_ORDER.index(normalize_status(status))


def sort_statuses(
    statuses: Iterable[StatusLike],
    *,
    unique: bool = False,
) -> tuple[RoadmapStatus, ...]:
    normalized = [normalize_status(status) for status in statuses]
    if unique:
        normalized = list(dict.fromkeys(normalized))
    return tuple(sorted(normalized, key=status_rank))


def is_complete(status: StatusLike) -> bool:
    return normalize_status(status) in COMPLETE_STATUSES


def is_active(status: StatusLike) -> bool:
    return normalize_status(status) in ACTIVE_STATUSES


def is_actionable(status: StatusLike) -> bool:
    return normalize_status(status) in ACTIONABLE_STATUSES


def is_open(status: StatusLike) -> bool:
    return normalize_status(status) in OPEN_STATUSES


def is_terminal(status: StatusLike) -> bool:
    return normalize_status(status) in TERMINAL_STATUSES


def is_blocked(status: StatusLike) -> bool:
    return normalize_status(status) is RoadmapStatus.BLOCKED


def is_planned(status: StatusLike) -> bool:
    return normalize_status(status) is RoadmapStatus.PLANNED


def all_statuses() -> tuple[RoadmapStatus, ...]:
    return STATUS_ORDER


def status_metadata(status: StatusLike) -> dict[str, object]:
    normalized = normalize_status(status)
    return {
        "value": normalized.value,
        "label": STATUS_LABELS[normalized],
        "emoji": STATUS_EMOJIS[normalized],
        "ansi_color": STATUS_ANSI_COLORS[normalized],
        "rank": status_rank(normalized),
        "complete": is_complete(normalized),
        "active": is_active(normalized),
        "actionable": is_actionable(normalized),
        "open": is_open(normalized),
        "terminal": is_terminal(normalized),
        "blocked": is_blocked(normalized),
        "planned": is_planned(normalized),
    }


__all__ = (
    "ACTIONABLE_STATUSES",
    "ACTIVE_STATUSES",
    "ALLOWED_STATUS_VALUES",
    "ANSI_RESET",
    "COMPLETE_STATUSES",
    "OPEN_STATUSES",
    "RoadmapStatus",
    "STATUS_ANSI_COLORS",
    "STATUS_EMOJIS",
    "STATUS_LABELS",
    "STATUS_ORDER",
    "StatusLike",
    "TERMINAL_STATUSES",
    "all_statuses",
    "format_status",
    "get_status_color",
    "get_status_emoji",
    "get_status_label",
    "is_actionable",
    "is_active",
    "is_blocked",
    "is_complete",
    "is_open",
    "is_planned",
    "is_terminal",
    "is_valid_status",
    "normalize_status",
    "sort_statuses",
    "status_metadata",
    "status_rank",
)
