"""
Read-only roadmap query utilities for the Nexa Provider Platform.

The functions in this module operate on immutable ``Milestone`` sequences and
``RoadmapSnapshot`` objects. They never mutate source records and always return
new tuples, immutable mappings, scalar counts, or existing milestone objects.

All hierarchy operations use milestone ``number`` and ``parent_number`` values.
Stable identity lookups use ``record_id``.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from types import MappingProxyType
from typing import Callable, Final, Iterable, Mapping, Sequence, TypeAlias

from .models import Milestone, RoadmapSnapshot
from .statuses import (
    RoadmapStatus,
    StatusLike,
    normalize_status,
    status_rank,
)


MilestoneSource: TypeAlias = Iterable[Milestone] | RoadmapSnapshot
MilestonePredicate: TypeAlias = Callable[[Milestone], bool]
MilestoneKey: TypeAlias = Callable[[Milestone], object]

DEFAULT_SEARCH_FIELDS: Final[tuple[str, ...]] = (
    "number",
    "record_id",
    "title",
    "semantic_path",
    "priority",
    "verification_state",
    "notes",
)

_ALLOWED_SEARCH_FIELDS: Final[frozenset[str]] = frozenset(
    DEFAULT_SEARCH_FIELDS
)


class RoadmapQueryError(ValueError):
    """Base exception for invalid roadmap queries."""


class MilestoneNotFoundError(LookupError):
    """Raised when a required milestone cannot be found."""


class DuplicateMilestoneError(RoadmapQueryError):
    """Raised when a field expected to be unique contains duplicates."""


class InvalidQueryFieldError(RoadmapQueryError):
    """Raised when an unsupported query field is requested."""


def _as_tuple(source: MilestoneSource) -> tuple[Milestone, ...]:
    """Normalize a roadmap source into an immutable milestone tuple."""

    if isinstance(source, RoadmapSnapshot):
        return source.milestones

    try:
        records = tuple(source)
    except TypeError as exc:
        raise TypeError(
            "source must be a RoadmapSnapshot or iterable of Milestone objects"
        ) from exc

    if not all(isinstance(item, Milestone) for item in records):
        raise TypeError("source must contain only Milestone objects")
    return records


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str):
        raise TypeError(
            f"{field_name} must be a string, received {type(value).__name__}"
        )
    normalized = value.strip()
    if not normalized:
        raise RoadmapQueryError(f"{field_name} cannot be blank")
    return normalized


def _normalize_case(value: str, *, case_sensitive: bool) -> str:
    return value if case_sensitive else value.casefold()


def _optional_text_matches(
    candidate: str | None,
    expected: str,
    *,
    case_sensitive: bool,
) -> bool:
    if candidate is None:
        return False
    return _normalize_case(
        candidate,
        case_sensitive=case_sensitive,
    ) == _normalize_case(
        expected,
        case_sensitive=case_sensitive,
    )


def _searchable_value(milestone: Milestone, field: str) -> str:
    value = getattr(milestone, field)
    if value is None:
        return ""
    if isinstance(value, tuple):
        return " ".join(str(item) for item in value)
    return str(value)


def all_milestones(source: MilestoneSource) -> tuple[Milestone, ...]:
    """Return all milestones as an immutable tuple."""

    return _as_tuple(source)


def build_number_index(
    source: MilestoneSource,
) -> Mapping[str, Milestone]:
    """Build an immutable number-to-milestone index."""

    records = _as_tuple(source)
    validate_unique_numbers(records)
    return MappingProxyType({item.number: item for item in records})


def build_record_id_index(
    source: MilestoneSource,
) -> Mapping[str, Milestone]:
    """Build an immutable stable-identity index."""

    records = _as_tuple(source)
    validate_unique_record_ids(records)
    return MappingProxyType({item.record_id: item for item in records})


def has_number(source: MilestoneSource, number: str) -> bool:
    """Return whether a milestone number exists."""

    target = _require_text(number, "number")
    return any(item.number == target for item in _as_tuple(source))


def has_record(source: MilestoneSource, record_id: str) -> bool:
    """Return whether a stable record ID exists."""

    target = _require_text(record_id, "record_id")
    return any(item.record_id == target for item in _as_tuple(source))


def get_by_number(
    source: MilestoneSource,
    number: str,
    *,
    required: bool = True,
) -> Milestone | None:
    """Find one milestone by exact visible number."""

    target = _require_text(number, "number")
    for milestone in _as_tuple(source):
        if milestone.number == target:
            return milestone

    if required:
        raise MilestoneNotFoundError(
            f"No roadmap milestone found with number {target!r}"
        )
    return None


def get_by_record_id(
    source: MilestoneSource,
    record_id: str,
    *,
    required: bool = True,
) -> Milestone | None:
    """Find one milestone by stable record identity."""

    target = _require_text(record_id, "record_id")
    for milestone in _as_tuple(source):
        if milestone.record_id == target:
            return milestone

    if required:
        raise MilestoneNotFoundError(
            f"No roadmap milestone found with record_id {target!r}"
        )
    return None


def get_by_title(
    source: MilestoneSource,
    title: str,
    *,
    case_sensitive: bool = False,
    required: bool = True,
) -> Milestone | None:
    """
    Find exactly one milestone by title.

    A duplicate exact title raises ``DuplicateMilestoneError``.
    """

    target = _require_text(title, "title")
    comparable = _normalize_case(target, case_sensitive=case_sensitive)
    matches = tuple(
        item
        for item in _as_tuple(source)
        if _normalize_case(
            item.title,
            case_sensitive=case_sensitive,
        ) == comparable
    )

    if len(matches) > 1:
        raise DuplicateMilestoneError(
            f"Multiple milestones have the title {target!r}"
        )
    if matches:
        return matches[0]
    if required:
        raise MilestoneNotFoundError(
            f"No roadmap milestone found with title {target!r}"
        )
    return None


def find_by_title(
    source: MilestoneSource,
    text: str,
    *,
    case_sensitive: bool = False,
) -> tuple[Milestone, ...]:
    """Return milestones whose titles contain the supplied text."""

    target = _require_text(text, "text")
    comparable = _normalize_case(target, case_sensitive=case_sensitive)
    return tuple(
        item
        for item in _as_tuple(source)
        if comparable in _normalize_case(
            item.title,
            case_sensitive=case_sensitive,
        )
    )


def get_roots(source: MilestoneSource) -> tuple[Milestone, ...]:
    """Return root milestones in source order."""

    return tuple(item for item in _as_tuple(source) if item.is_root)


def get_parent(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    required: bool = False,
) -> Milestone | None:
    """
    Return a milestone's parent.

    ``milestone`` may be a ``Milestone`` instance or visible milestone number.
    Root milestones return ``None`` unless ``required`` is true.
    """

    records = _as_tuple(source)
    current = (
        milestone
        if isinstance(milestone, Milestone)
        else get_by_number(records, milestone)
    )

    if current.parent_number is None:
        if required:
            raise MilestoneNotFoundError(
                f"Milestone {current.number!r} is a root and has no parent"
            )
        return None

    return get_by_number(
        records,
        current.parent_number,
        required=required,
    )


def get_children(
    source: MilestoneSource,
    milestone: Milestone | str,
) -> tuple[Milestone, ...]:
    """Return direct children of a milestone in source order."""

    records = _as_tuple(source)
    current = (
        milestone
        if isinstance(milestone, Milestone)
        else get_by_number(records, milestone)
    )
    return tuple(
        item for item in records if item.parent_number == current.number
    )


def get_ancestors(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    nearest_first: bool = False,
) -> tuple[Milestone, ...]:
    """Return all ancestors, root-first by default."""

    records = _as_tuple(source)
    current = (
        milestone
        if isinstance(milestone, Milestone)
        else get_by_number(records, milestone)
    )
    index = build_number_index(records)
    ancestors: list[Milestone] = []
    seen: set[str] = set()

    parent_number = current.parent_number
    while parent_number is not None:
        if parent_number in seen:
            raise RoadmapQueryError(
                f"Hierarchy cycle detected at {parent_number!r}"
            )
        seen.add(parent_number)

        parent = index.get(parent_number)
        if parent is None:
            raise MilestoneNotFoundError(
                f"Missing parent milestone {parent_number!r} "
                f"for {current.number!r}"
            )
        ancestors.append(parent)
        parent_number = parent.parent_number

    if not nearest_first:
        ancestors.reverse()
    return tuple(ancestors)


def get_descendants(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    include_self: bool = False,
) -> tuple[Milestone, ...]:
    """Return all descendants in deterministic depth-first source order."""

    records = _as_tuple(source)
    current = (
        milestone
        if isinstance(milestone, Milestone)
        else get_by_number(records, milestone)
    )

    children_by_parent: dict[str, list[Milestone]] = defaultdict(list)
    for item in records:
        if item.parent_number is not None:
            children_by_parent[item.parent_number].append(item)

    result: list[Milestone] = [current] if include_self else []
    visiting: set[str] = set()

    def visit(parent: Milestone) -> None:
        if parent.number in visiting:
            raise RoadmapQueryError(
                f"Hierarchy cycle detected at {parent.number!r}"
            )
        visiting.add(parent.number)
        for child in children_by_parent.get(parent.number, ()):
            result.append(child)
            visit(child)
        visiting.remove(parent.number)

    visit(current)
    return tuple(result)


def get_siblings(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    include_self: bool = False,
) -> tuple[Milestone, ...]:
    """Return milestones sharing the same parent."""

    records = _as_tuple(source)
    current = (
        milestone
        if isinstance(milestone, Milestone)
        else get_by_number(records, milestone)
    )

    siblings = tuple(
        item
        for item in records
        if item.parent_number == current.parent_number
        and (include_self or item.number != current.number)
    )
    return siblings


def filter_records(
    source: MilestoneSource,
    predicate: MilestonePredicate,
) -> tuple[Milestone, ...]:
    """Return milestones accepted by a predicate."""

    if not callable(predicate):
        raise TypeError("predicate must be callable")
    return tuple(item for item in _as_tuple(source) if predicate(item))


def filter_by_status(
    source: MilestoneSource,
    statuses: StatusLike | Iterable[StatusLike],
) -> tuple[Milestone, ...]:
    """Return milestones matching one or more lifecycle statuses."""

    if isinstance(statuses, (str, RoadmapStatus)):
        accepted = {normalize_status(statuses)}
    else:
        accepted = {normalize_status(value) for value in statuses}

    if not accepted:
        return ()
    return tuple(
        item for item in _as_tuple(source) if item.status in accepted
    )


def filter_by_priority(
    source: MilestoneSource,
    priorities: str | Iterable[str],
    *,
    case_sensitive: bool = False,
    include_unset: bool = False,
) -> tuple[Milestone, ...]:
    """Return milestones matching one or more priority labels."""

    if isinstance(priorities, str):
        raw_priorities = (priorities,)
    else:
        raw_priorities = tuple(priorities)

    accepted = {
        _normalize_case(
            _require_text(value, "priority"),
            case_sensitive=case_sensitive,
        )
        for value in raw_priorities
    }

    return tuple(
        item
        for item in _as_tuple(source)
        if (
            item.priority is None
            and include_unset
        )
        or (
            item.priority is not None
            and _normalize_case(
                item.priority,
                case_sensitive=case_sensitive,
            ) in accepted
        )
    )


def filter_by_depth(
    source: MilestoneSource,
    depths: int | Iterable[int],
) -> tuple[Milestone, ...]:
    """Return milestones whose hierarchy depth is accepted."""

    if isinstance(depths, bool):
        raise TypeError("depth cannot be a boolean")
    if isinstance(depths, int):
        accepted = {depths}
    else:
        accepted = set(depths)

    for depth in accepted:
        if isinstance(depth, bool) or not isinstance(depth, int):
            raise TypeError("all depths must be integers")
        if depth < 0:
            raise RoadmapQueryError("depth cannot be negative")

    return tuple(
        item for item in _as_tuple(source) if item.depth in accepted
    )


def filter_by_parent(
    source: MilestoneSource,
    parent_number: str | None,
) -> tuple[Milestone, ...]:
    """Return direct children of a parent number, or roots for ``None``."""

    if parent_number is not None:
        parent_number = _require_text(parent_number, "parent_number")
    return tuple(
        item
        for item in _as_tuple(source)
        if item.parent_number == parent_number
    )


def filter_by_dependency(
    source: MilestoneSource,
    dependency: str,
) -> tuple[Milestone, ...]:
    """Return milestones that directly declare a dependency."""

    target = _require_text(dependency, "dependency")
    return tuple(
        item
        for item in _as_tuple(source)
        if target in item.dependencies
    )


def filter_by_semantic_path(
    source: MilestoneSource,
    path: str,
    *,
    exact: bool = False,
    case_sensitive: bool = False,
) -> tuple[Milestone, ...]:
    """Filter by exact semantic path or semantic-path prefix."""

    target = _require_text(path, "path").rstrip("/")
    comparable = _normalize_case(target, case_sensitive=case_sensitive)

    def matches(item: Milestone) -> bool:
        candidate = _normalize_case(
            item.semantic_path.rstrip("/"),
            case_sensitive=case_sensitive,
        )
        if exact:
            return candidate == comparable
        return (
            candidate == comparable
            or candidate.startswith(comparable + "/")
            or candidate.startswith(comparable + " /")
        )

    return tuple(item for item in _as_tuple(source) if matches(item))


def search(
    source: MilestoneSource,
    query: str,
    *,
    fields: Iterable[str] = DEFAULT_SEARCH_FIELDS,
    case_sensitive: bool = False,
    match_all_terms: bool = True,
) -> tuple[Milestone, ...]:
    """
    Search selected milestone fields.

    Terms are whitespace-delimited. By default every term must appear somewhere
    across the selected fields. Set ``match_all_terms=False`` for OR behavior.
    """

    text = _require_text(query, "query")
    selected_fields = tuple(fields)
    if not selected_fields:
        raise RoadmapQueryError("fields cannot be empty")

    invalid = tuple(
        field for field in selected_fields
        if field not in _ALLOWED_SEARCH_FIELDS
    )
    if invalid:
        raise InvalidQueryFieldError(
            "Unsupported search field(s): " + ", ".join(invalid)
        )

    terms = tuple(
        _normalize_case(term, case_sensitive=case_sensitive)
        for term in text.split()
        if term
    )

    def matches(item: Milestone) -> bool:
        haystack = " ".join(
            _searchable_value(item, field)
            for field in selected_fields
        )
        haystack = _normalize_case(
            haystack,
            case_sensitive=case_sensitive,
        )
        predicate = all if match_all_terms else any
        return predicate(term in haystack for term in terms)

    return tuple(item for item in _as_tuple(source) if matches(item))


def sort_by_sequence(
    source: MilestoneSource,
    *,
    reverse: bool = False,
) -> tuple[Milestone, ...]:
    """Return milestones sorted by canonical sequence."""

    return tuple(
        sorted(
            _as_tuple(source),
            key=lambda item: (item.sequence, item.number),
            reverse=reverse,
        )
    )


def sort_by_number(
    source: MilestoneSource,
    *,
    reverse: bool = False,
) -> tuple[Milestone, ...]:
    """Sort by hierarchy-aware milestone number components."""

    def number_key(item: Milestone) -> tuple[int, ...]:
        visible = item.number[1:]
        return tuple(int(part) for part in visible.split("."))

    return tuple(
        sorted(_as_tuple(source), key=number_key, reverse=reverse)
    )


def sort_by_title(
    source: MilestoneSource,
    *,
    reverse: bool = False,
    case_sensitive: bool = False,
) -> tuple[Milestone, ...]:
    """Return milestones sorted by title and then sequence."""

    return tuple(
        sorted(
            _as_tuple(source),
            key=lambda item: (
                _normalize_case(
                    item.title,
                    case_sensitive=case_sensitive,
                ),
                item.sequence,
            ),
            reverse=reverse,
        )
    )


def sort_by_status(
    source: MilestoneSource,
    *,
    reverse: bool = False,
) -> tuple[Milestone, ...]:
    """Return milestones in canonical status display order."""

    return tuple(
        sorted(
            _as_tuple(source),
            key=lambda item: (status_rank(item.status), item.sequence),
            reverse=reverse,
        )
    )


def group_by_status(
    source: MilestoneSource,
) -> Mapping[RoadmapStatus, tuple[Milestone, ...]]:
    """Group milestones by lifecycle status."""

    grouped: dict[RoadmapStatus, list[Milestone]] = defaultdict(list)
    for item in _as_tuple(source):
        grouped[item.status].append(item)
    return MappingProxyType(
        {key: tuple(value) for key, value in grouped.items()}
    )


def group_by_parent(
    source: MilestoneSource,
) -> Mapping[str | None, tuple[Milestone, ...]]:
    """Group milestones by direct parent number."""

    grouped: dict[str | None, list[Milestone]] = defaultdict(list)
    for item in _as_tuple(source):
        grouped[item.parent_number].append(item)
    return MappingProxyType(
        {key: tuple(value) for key, value in grouped.items()}
    )


def group_by_depth(
    source: MilestoneSource,
) -> Mapping[int, tuple[Milestone, ...]]:
    """Group milestones by hierarchy depth."""

    grouped: dict[int, list[Milestone]] = defaultdict(list)
    for item in _as_tuple(source):
        grouped[item.depth].append(item)
    return MappingProxyType(
        {key: tuple(value) for key, value in grouped.items()}
    )


def group_by_priority(
    source: MilestoneSource,
) -> Mapping[str | None, tuple[Milestone, ...]]:
    """Group milestones by priority, preserving unset values as ``None``."""

    grouped: dict[str | None, list[Milestone]] = defaultdict(list)
    for item in _as_tuple(source):
        grouped[item.priority].append(item)
    return MappingProxyType(
        {key: tuple(value) for key, value in grouped.items()}
    )


def count_by_status(
    source: MilestoneSource,
) -> Mapping[RoadmapStatus, int]:
    """Count milestones by lifecycle status."""

    counts = Counter(item.status for item in _as_tuple(source))
    return MappingProxyType(dict(counts))


def count_by_depth(
    source: MilestoneSource,
) -> Mapping[int, int]:
    """Count milestones by hierarchy depth."""

    counts = Counter(item.depth for item in _as_tuple(source))
    return MappingProxyType(dict(counts))


def count_by_priority(
    source: MilestoneSource,
) -> Mapping[str | None, int]:
    """Count milestones by priority label."""

    counts = Counter(item.priority for item in _as_tuple(source))
    return MappingProxyType(dict(counts))


def validate_unique_numbers(source: MilestoneSource) -> bool:
    """Validate that every milestone number is unique."""

    seen: set[str] = set()
    duplicates: list[str] = []
    for item in _as_tuple(source):
        if item.number in seen and item.number not in duplicates:
            duplicates.append(item.number)
        seen.add(item.number)

    if duplicates:
        raise DuplicateMilestoneError(
            "Duplicate milestone number(s): " + ", ".join(duplicates)
        )
    return True


def validate_unique_record_ids(source: MilestoneSource) -> bool:
    """Validate that every stable record ID is unique."""

    seen: set[str] = set()
    duplicates: list[str] = []
    for item in _as_tuple(source):
        if item.record_id in seen and item.record_id not in duplicates:
            duplicates.append(item.record_id)
        seen.add(item.record_id)

    if duplicates:
        raise DuplicateMilestoneError(
            "Duplicate record_id value(s): " + ", ".join(duplicates)
        )
    return True


def validate_parent_links(source: MilestoneSource) -> bool:
    """Validate that all non-root parent references exist."""

    records = _as_tuple(source)
    numbers = {item.number for item in records}
    missing = tuple(
        (item.number, item.parent_number)
        for item in records
        if item.parent_number is not None
        and item.parent_number not in numbers
    )
    if missing:
        rendered = ", ".join(
            f"{child}->{parent}" for child, parent in missing
        )
        raise RoadmapQueryError(
            "Missing roadmap parent link(s): " + rendered
        )
    return True


def query(
    source: MilestoneSource,
    *,
    predicate: MilestonePredicate | None = None,
    sort_key: MilestoneKey | None = None,
    reverse: bool = False,
    limit: int | None = None,
) -> tuple[Milestone, ...]:
    """
    Apply a general read-only predicate, sort, and limit query.

    This is intentionally small and deterministic; specialized helpers remain
    preferable for common roadmap operations.
    """

    records = _as_tuple(source)

    if predicate is not None:
        if not callable(predicate):
            raise TypeError("predicate must be callable")
        records = tuple(item for item in records if predicate(item))

    if sort_key is not None:
        if not callable(sort_key):
            raise TypeError("sort_key must be callable")
        records = tuple(
            sorted(records, key=sort_key, reverse=reverse)
        )
    elif reverse:
        records = tuple(reversed(records))

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int):
            raise TypeError("limit must be an integer or None")
        if limit < 0:
            raise RoadmapQueryError("limit cannot be negative")
        records = records[:limit]

    return records


__all__ = (
    "DEFAULT_SEARCH_FIELDS",
    "DuplicateMilestoneError",
    "InvalidQueryFieldError",
    "MilestoneKey",
    "MilestoneNotFoundError",
    "MilestonePredicate",
    "MilestoneSource",
    "RoadmapQueryError",
    "all_milestones",
    "build_number_index",
    "build_record_id_index",
    "count_by_depth",
    "count_by_priority",
    "count_by_status",
    "filter_by_dependency",
    "filter_by_depth",
    "filter_by_parent",
    "filter_by_priority",
    "filter_by_semantic_path",
    "filter_by_status",
    "filter_records",
    "find_by_title",
    "get_ancestors",
    "get_by_number",
    "get_by_record_id",
    "get_by_title",
    "get_children",
    "get_descendants",
    "get_parent",
    "get_roots",
    "get_siblings",
    "group_by_depth",
    "group_by_parent",
    "group_by_priority",
    "group_by_status",
    "has_number",
    "has_record",
    "query",
    "search",
    "sort_by_number",
    "sort_by_sequence",
    "sort_by_status",
    "sort_by_title",
    "validate_parent_links",
    "validate_unique_numbers",
    "validate_unique_record_ids",
)
