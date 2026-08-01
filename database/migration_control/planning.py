"""Deterministic dependency planning for approved migration catalogues."""
from __future__ import annotations

from heapq import heappop, heappush

from .checksums import ordered_plan_digest
from .contracts import MigrationCatalogue, MigrationDefinition, MigrationPlan
from .errors import MigrationCycleError, MigrationDependencyError, MigrationOrderError


class MigrationPlanner:
    def create_plan(self, catalogue: MigrationCatalogue) -> MigrationPlan:
        by_id = dict(catalogue.by_id())
        for definition in catalogue.definitions:
            missing = [dependency for dependency in definition.depends_on if dependency not in by_id]
            if missing:
                raise MigrationDependencyError(
                    f"{definition.identity.migration_id} has missing dependencies: {', '.join(sorted(missing))}"
                )
        indegree = {migration_id: 0 for migration_id in by_id}
        children: dict[str, set[str]] = {migration_id: set() for migration_id in by_id}
        for definition in catalogue.definitions:
            current = definition.identity.migration_id
            indegree[current] = len(definition.depends_on)
            for dependency in definition.depends_on:
                children[dependency].add(current)
        ready: list[tuple[int, str]] = []
        for migration_id, degree in indegree.items():
            if degree == 0:
                item = by_id[migration_id]
                heappush(ready, (item.identity.sequence_number, migration_id))
        ordered: list[MigrationDefinition] = []
        while ready:
            _, migration_id = heappop(ready)
            item = by_id[migration_id]
            ordered.append(item)
            for child in sorted(children[migration_id]):
                indegree[child] -= 1
                if indegree[child] == 0:
                    child_item = by_id[child]
                    heappush(ready, (child_item.identity.sequence_number, child))
        if len(ordered) != len(by_id):
            unresolved = sorted(migration_id for migration_id, degree in indegree.items() if degree > 0)
            raise MigrationCycleError(f"migration dependency cycle detected: {', '.join(unresolved)}")
        sequences = [item.identity.sequence_number for item in ordered]
        if sequences != sorted(sequences):
            raise MigrationOrderError("dependency order conflicts with approved sequence numbers.")
        rollback = tuple(reversed(ordered))
        rows = [
            {
                "migration_id": item.identity.migration_id,
                "milestone_id": item.identity.milestone_id,
                "sequence_number": item.identity.sequence_number,
                "depends_on": list(item.depends_on),
                "forward_sha256": item.forward.sha256,
                "rollback_sha256": item.rollback.sha256,
            }
            for item in ordered
        ]
        return MigrationPlan(
            forward_order=tuple(ordered),
            rollback_order=rollback,
            plan_checksum=ordered_plan_digest(rows),
            manifest_digest=catalogue.manifest_digest,
        )


__all__ = ["MigrationPlanner"]
