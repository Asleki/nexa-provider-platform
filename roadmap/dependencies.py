"""
Immutable dependency graph utilities for the Nexa Provider Platform roadmap.

The canonical roadmap currently permits milestones with no dependency edges.
This module also supports future dependency-rich roadmaps through validation,
traversal, cycle detection, topological sorting, readiness analysis, and
dependency summaries.
"""

from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from types import MappingProxyType
from typing import Iterable, Mapping, TypeAlias

from .models import Milestone
from .queries import MilestoneSource, all_milestones, build_number_index, get_by_number
from .statuses import COMPLETE_STATUSES, RoadmapStatus, StatusLike, normalize_status

DependencyKey: TypeAlias = str


class RoadmapDependencyError(ValueError):
    """Base exception for dependency graph errors."""


class MissingDependencyError(RoadmapDependencyError):
    """Raised when a dependency reference cannot be resolved."""


class DependencyCycleError(RoadmapDependencyError):
    """Raised when a dependency cycle is detected."""


class DuplicateDependencyError(RoadmapDependencyError):
    """Raised for duplicate direct dependency declarations."""


@dataclass(frozen=True, slots=True)
class DependencyValidationResult:
    total_milestones: int
    milestones_with_dependencies: int
    dependency_edges: int
    missing_dependencies: tuple[tuple[str, str], ...]
    duplicate_dependencies: tuple[tuple[str, str], ...]
    self_dependencies: tuple[str, ...]
    cycles: tuple[tuple[str, ...], ...]

    @property
    def is_valid(self) -> bool:
        return not (
            self.missing_dependencies
            or self.duplicate_dependencies
            or self.self_dependencies
            or self.cycles
        )

    @property
    def error_count(self) -> int:
        return (
            len(self.missing_dependencies)
            + len(self.duplicate_dependencies)
            + len(self.self_dependencies)
            + len(self.cycles)
        )


@dataclass(frozen=True, slots=True)
class DependencySummary:
    milestone: Milestone
    direct_dependencies: tuple[Milestone, ...]
    transitive_dependencies: tuple[Milestone, ...]
    direct_dependents: tuple[Milestone, ...]
    transitive_dependents: tuple[Milestone, ...]
    unresolved_dependency_numbers: tuple[str, ...]
    blocking_dependencies: tuple[Milestone, ...]
    is_ready: bool


def _complete_set(values: Iterable[StatusLike]) -> frozenset[RoadmapStatus]:
    return frozenset(normalize_status(value) for value in values)


def dependency_numbers(milestone: Milestone) -> tuple[str, ...]:
    if not isinstance(milestone, Milestone):
        raise TypeError("milestone must be a Milestone")
    return milestone.dependencies


def has_dependencies(milestone: Milestone) -> bool:
    return bool(dependency_numbers(milestone))


def build_dependency_index(source: MilestoneSource) -> Mapping[str, tuple[str, ...]]:
    return MappingProxyType({
        item.number: tuple(item.dependencies)
        for item in all_milestones(source)
    })


def build_dependents_index(
    source: MilestoneSource,
    *,
    include_missing: bool = False,
) -> Mapping[str, tuple[str, ...]]:
    records = all_milestones(source)
    known = {item.number for item in records}
    grouped: dict[str, list[str]] = defaultdict(list)
    for item in records:
        for dependency in item.dependencies:
            if include_missing or dependency in known:
                grouped[dependency].append(item.number)
    return MappingProxyType({key: tuple(value) for key, value in grouped.items()})


def unresolved_dependencies(
    source: MilestoneSource,
    milestone: Milestone | str,
) -> tuple[str, ...]:
    records = all_milestones(source)
    current = milestone if isinstance(milestone, Milestone) else get_by_number(records, milestone)
    known = {item.number for item in records}
    return tuple(dep for dep in current.dependencies if dep not in known)


def direct_dependencies(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    strict: bool = True,
) -> tuple[Milestone, ...]:
    records = all_milestones(source)
    current = milestone if isinstance(milestone, Milestone) else get_by_number(records, milestone)
    index = build_number_index(records)
    resolved: list[Milestone] = []
    missing: list[str] = []
    for number in current.dependencies:
        found = index.get(number)
        if found is None:
            missing.append(number)
        else:
            resolved.append(found)
    if missing and strict:
        raise MissingDependencyError(
            f"Milestone {current.number!r} has missing dependencies: " + ", ".join(missing)
        )
    return tuple(resolved)


def direct_dependents(
    source: MilestoneSource,
    milestone: Milestone | str,
) -> tuple[Milestone, ...]:
    records = all_milestones(source)
    current = milestone if isinstance(milestone, Milestone) else get_by_number(records, milestone)
    return tuple(item for item in records if current.number in item.dependencies)


def transitive_dependencies(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    include_self: bool = False,
    strict: bool = True,
) -> tuple[Milestone, ...]:
    records = all_milestones(source)
    current = milestone if isinstance(milestone, Milestone) else get_by_number(records, milestone)
    index = build_number_index(records)
    result: list[Milestone] = [current] if include_self else []
    emitted: set[str] = {current.number} if include_self else set()
    stack: list[str] = []

    def visit(node: Milestone) -> None:
        stack.append(node.number)
        for dep_number in node.dependencies:
            dependency = index.get(dep_number)
            if dependency is None:
                if strict:
                    raise MissingDependencyError(
                        f"Milestone {node.number!r} has missing dependency {dep_number!r}"
                    )
                continue
            if dep_number in stack:
                start = stack.index(dep_number)
                cycle = tuple(stack[start:] + [dep_number])
                raise DependencyCycleError(
                    "Dependency cycle detected: " + " -> ".join(cycle)
                )
            if dep_number not in emitted:
                emitted.add(dep_number)
                result.append(dependency)
                visit(dependency)
        stack.pop()

    visit(current)
    return tuple(result)


def transitive_dependents(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    include_self: bool = False,
) -> tuple[Milestone, ...]:
    records = all_milestones(source)
    current = milestone if isinstance(milestone, Milestone) else get_by_number(records, milestone)
    index = build_number_index(records)
    reverse = build_dependents_index(records)
    result: list[Milestone] = [current] if include_self else []
    seen = {current.number}
    queue: deque[str] = deque(reverse.get(current.number, ()))
    while queue:
        number = queue.popleft()
        if number in seen:
            continue
        seen.add(number)
        result.append(index[number])
        queue.extend(reverse.get(number, ()))
    return tuple(result)


def dependency_depth(
    source: MilestoneSource,
    milestone: Milestone | str,
) -> int:
    records = all_milestones(source)
    current = milestone if isinstance(milestone, Milestone) else get_by_number(records, milestone)
    index = build_number_index(records)
    memo: dict[str, int] = {}
    visiting: set[str] = set()

    def depth(node: Milestone) -> int:
        if node.number in memo:
            return memo[node.number]
        if node.number in visiting:
            raise DependencyCycleError(f"Dependency cycle detected at {node.number!r}")
        visiting.add(node.number)
        depths: list[int] = []
        for dep_number in node.dependencies:
            dependency = index.get(dep_number)
            if dependency is None:
                raise MissingDependencyError(
                    f"Milestone {node.number!r} has missing dependency {dep_number!r}"
                )
            depths.append(depth(dependency))
        visiting.remove(node.number)
        value = 0 if not depths else 1 + max(depths)
        memo[node.number] = value
        return value

    return depth(current)


def dependency_path_exists(
    source: MilestoneSource,
    start: Milestone | str,
    target: Milestone | str,
) -> bool:
    records = all_milestones(source)
    start_item = start if isinstance(start, Milestone) else get_by_number(records, start)
    target_item = target if isinstance(target, Milestone) else get_by_number(records, target)
    return any(
        item.number == target_item.number
        for item in transitive_dependencies(records, start_item)
    )


def missing_dependency_references(
    source: MilestoneSource,
) -> tuple[tuple[str, str], ...]:
    records = all_milestones(source)
    known = {item.number for item in records}
    return tuple(
        (item.number, dep)
        for item in records
        for dep in item.dependencies
        if dep not in known
    )


def duplicate_dependency_references(
    source: MilestoneSource,
) -> tuple[tuple[str, str], ...]:
    result: list[tuple[str, str]] = []
    for item in all_milestones(source):
        seen: set[str] = set()
        emitted: set[str] = set()
        for dep in item.dependencies:
            if dep in seen and dep not in emitted:
                result.append((item.number, dep))
                emitted.add(dep)
            seen.add(dep)
    return tuple(result)


def self_dependencies(source: MilestoneSource) -> tuple[str, ...]:
    return tuple(
        item.number for item in all_milestones(source)
        if item.number in item.dependencies
    )


def find_dependency_cycles(
    source: MilestoneSource,
) -> tuple[tuple[str, ...], ...]:
    records = all_milestones(source)
    index = build_number_index(records)
    state = {item.number: 0 for item in records}
    stack: list[str] = []
    cycles: list[tuple[str, ...]] = []
    seen_cycles: set[tuple[str, ...]] = set()

    def canonical(cycle: tuple[str, ...]) -> tuple[str, ...]:
        body = cycle[:-1]
        rotations = [body[i:] + body[:i] for i in range(len(body))]
        smallest = min(rotations)
        return smallest + (smallest[0],)

    def visit(number: str) -> None:
        state[number] = 1
        stack.append(number)
        for dep in index[number].dependencies:
            if dep not in index:
                continue
            if state[dep] == 0:
                visit(dep)
            elif state[dep] == 1:
                start = stack.index(dep)
                cycle = canonical(tuple(stack[start:] + [dep]))
                if cycle not in seen_cycles:
                    seen_cycles.add(cycle)
                    cycles.append(cycle)
        stack.pop()
        state[number] = 2

    for item in records:
        if state[item.number] == 0:
            visit(item.number)
    return tuple(cycles)


def validate_dependencies(
    source: MilestoneSource,
    *,
    raise_on_error: bool = False,
) -> DependencyValidationResult:
    records = all_milestones(source)
    result = DependencyValidationResult(
        total_milestones=len(records),
        milestones_with_dependencies=sum(bool(item.dependencies) for item in records),
        dependency_edges=sum(len(item.dependencies) for item in records),
        missing_dependencies=missing_dependency_references(records),
        duplicate_dependencies=duplicate_dependency_references(records),
        self_dependencies=self_dependencies(records),
        cycles=find_dependency_cycles(records),
    )
    if raise_on_error and not result.is_valid:
        raise RoadmapDependencyError(
            f"Dependency validation failed with {result.error_count} error(s)"
        )
    return result


def topological_order(
    source: MilestoneSource,
    *,
    strict: bool = True,
) -> tuple[Milestone, ...]:
    records = all_milestones(source)
    index = build_number_index(records)
    missing = missing_dependency_references(records)
    if missing and strict:
        raise MissingDependencyError(
            "Cannot topologically sort graph with missing dependencies"
        )

    indegree = {item.number: 0 for item in records}
    reverse: dict[str, list[str]] = defaultdict(list)
    for item in records:
        for dep in item.dependencies:
            if dep in index:
                indegree[item.number] += 1
                reverse[dep].append(item.number)

    available = sorted(
        (item for item in records if indegree[item.number] == 0),
        key=lambda item: (item.sequence, item.number),
    )
    ordered: list[Milestone] = []

    while available:
        current = available.pop(0)
        ordered.append(current)
        for dependent_number in reverse.get(current.number, ()):
            indegree[dependent_number] -= 1
            if indegree[dependent_number] == 0:
                available.append(index[dependent_number])
        available.sort(key=lambda item: (item.sequence, item.number))

    if len(ordered) != len(records):
        raise DependencyCycleError("Cannot topologically sort cyclic graph")
    return tuple(ordered)


def blocking_dependencies(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
    transitive: bool = False,
) -> tuple[Milestone, ...]:
    accepted = _complete_set(complete_statuses)
    dependencies = (
        transitive_dependencies(source, milestone)
        if transitive
        else direct_dependencies(source, milestone)
    )
    return tuple(item for item in dependencies if item.status not in accepted)


def is_dependency_ready(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
    require_dependencies: bool = False,
    transitive: bool = False,
) -> bool:
    records = all_milestones(source)
    current = milestone if isinstance(milestone, Milestone) else get_by_number(records, milestone)
    if unresolved_dependencies(records, current):
        return False
    if require_dependencies and not current.dependencies:
        return False
    return not blocking_dependencies(
        records,
        current,
        complete_statuses=complete_statuses,
        transitive=transitive,
    )


def ready_milestones(
    source: MilestoneSource,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
    include_completed: bool = False,
    require_dependencies: bool = False,
) -> tuple[Milestone, ...]:
    records = all_milestones(source)
    accepted = _complete_set(complete_statuses)
    return tuple(
        item for item in records
        if (include_completed or item.status not in accepted)
        and is_dependency_ready(
            records,
            item,
            complete_statuses=accepted,
            require_dependencies=require_dependencies,
        )
    )


def blocked_by_dependencies(
    source: MilestoneSource,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
) -> tuple[Milestone, ...]:
    records = all_milestones(source)
    accepted = _complete_set(complete_statuses)
    return tuple(
        item for item in records
        if item.dependencies
        and (
            unresolved_dependencies(records, item)
            or blocking_dependencies(records, item, complete_statuses=accepted)
        )
    )


def dependency_summary(
    source: MilestoneSource,
    milestone: Milestone | str,
    *,
    complete_statuses: Iterable[StatusLike] = COMPLETE_STATUSES,
) -> DependencySummary:
    records = all_milestones(source)
    current = milestone if isinstance(milestone, Milestone) else get_by_number(records, milestone)
    unresolved = unresolved_dependencies(records, current)
    blockers = blocking_dependencies(
        records,
        current,
        complete_statuses=complete_statuses,
    ) if not unresolved else tuple(
        item for item in direct_dependencies(records, current, strict=False)
        if item.status not in _complete_set(complete_statuses)
    )
    return DependencySummary(
        milestone=current,
        direct_dependencies=direct_dependencies(records, current, strict=False),
        transitive_dependencies=transitive_dependencies(records, current, strict=False),
        direct_dependents=direct_dependents(records, current),
        transitive_dependents=transitive_dependents(records, current),
        unresolved_dependency_numbers=unresolved,
        blocking_dependencies=blockers,
        is_ready=not unresolved and not blockers,
    )


def dependency_edge_count(source: MilestoneSource) -> int:
    return sum(len(item.dependencies) for item in all_milestones(source))


def dependency_free_milestones(source: MilestoneSource) -> tuple[Milestone, ...]:
    return tuple(item for item in all_milestones(source) if not item.dependencies)


__all__ = (
    "DependencyCycleError",
    "DependencyKey",
    "DependencySummary",
    "DependencyValidationResult",
    "DuplicateDependencyError",
    "MissingDependencyError",
    "RoadmapDependencyError",
    "blocked_by_dependencies",
    "blocking_dependencies",
    "build_dependency_index",
    "build_dependents_index",
    "dependency_depth",
    "dependency_edge_count",
    "dependency_free_milestones",
    "dependency_numbers",
    "dependency_path_exists",
    "dependency_summary",
    "direct_dependencies",
    "direct_dependents",
    "duplicate_dependency_references",
    "find_dependency_cycles",
    "has_dependencies",
    "is_dependency_ready",
    "missing_dependency_references",
    "ready_milestones",
    "self_dependencies",
    "topological_order",
    "transitive_dependencies",
    "transitive_dependents",
    "unresolved_dependencies",
    "validate_dependencies",
)
