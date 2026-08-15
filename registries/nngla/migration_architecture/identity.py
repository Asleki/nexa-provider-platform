"""P006.7.11.2 deterministic canonical identity proposal controls."""
from __future__ import annotations

from dataclasses import dataclass
import re
from collections.abc import Iterable

from .contracts import (
    CANONICAL_NAMESPACE_CONTRACTS,
    CanonicalIdentityProposal,
    CanonicalObjectFamily,
    SourceIdentity,
)


_SUFFIX_6 = re.compile(r"(\d{6})$")


class CanonicalIdentityError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class AllocationConflict:
    canonical_id: str
    source_record_ids: tuple[str, ...]


class CanonicalIdentityAllocator:
    """Propose stable canonical IDs without writing to PostgreSQL.

    Bundle 16A uses governed six-digit source/candidate suffixes when the
    source family already carries one. This makes preview repeatable across
    batches and avoids unsafe MAX(id)+1 allocation. PostgreSQL collision checks
    are performed by later adapters before execution.
    """

    @staticmethod
    def _suffix(value: str) -> str:
        match = _SUFFIX_6.search(str(value))
        if match is None:
            raise CanonicalIdentityError(
                f"source/candidate identity {value!r} does not expose a governed six-digit suffix"
            )
        return match.group(1)

    def propose(
        self,
        *,
        source: SourceIdentity,
        object_family: CanonicalObjectFamily,
        preferred_identity: str | None = None,
    ) -> CanonicalIdentityProposal:
        contract = CANONICAL_NAMESPACE_CONTRACTS.get(object_family)
        if contract is None:
            raise CanonicalIdentityError(f"no Bundle 16A canonical namespace for {object_family.value}")

        basis = preferred_identity or source.candidate_id or source.source_record_id
        suffix = self._suffix(basis)
        canonical_id = f"{contract.prefix}{suffix}"
        if not contract.validates(canonical_id):
            raise CanonicalIdentityError(f"proposed canonical identity is invalid: {canonical_id}")
        return CanonicalIdentityProposal(
            source=source,
            object_family=object_family,
            canonical_id=canonical_id,
            allocation_basis=f"governed-six-digit-suffix:{basis}",
        )

    @staticmethod
    def detect_proposal_collisions(
        proposals: Iterable[CanonicalIdentityProposal],
    ) -> tuple[AllocationConflict, ...]:
        by_id: dict[str, list[str]] = {}
        for proposal in proposals:
            by_id.setdefault(proposal.canonical_id, []).append(proposal.source.source_record_id)
        return tuple(
            AllocationConflict(canonical_id, tuple(sorted(source_ids)))
            for canonical_id, source_ids in sorted(by_id.items())
            if len(set(source_ids)) > 1
        )


__all__ = [
    "CanonicalIdentityError",
    "AllocationConflict",
    "CanonicalIdentityAllocator",
]
