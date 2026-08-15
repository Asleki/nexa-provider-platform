"""P006.7.11 Bundle 16A migration-architecture contracts.

These contracts define source/candidate/canonical identity roles without
changing the locked P006.7.2-P006.7.10 domain models.  They are intentionally
storage-neutral so later PostgreSQL adapters can implement them additively.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class IdentifierRole(str, Enum):
    SOURCE_RECORD = "SOURCE_RECORD"
    CANDIDATE = "CANDIDATE"
    CANONICAL = "CANONICAL"
    NAME = "NAME"
    GEOMETRY = "GEOMETRY"
    LEGAL = "LEGAL"


class CanonicalObjectFamily(str, Enum):
    PLACE = "PLACE"
    ADMINISTRATIVE_AREA = "ADMINISTRATIVE_AREA"
    ROAD = "ROAD"
    GEOGRAPHIC_FEATURE = "GEOGRAPHIC_FEATURE"
    GEOMETRY = "GEOMETRY"
    ADDRESS = "ADDRESS"
    PARCEL = "PARCEL"
    TITLE = "TITLE"


@dataclass(frozen=True, slots=True)
class IdentifierNamespaceContract:
    object_family: CanonicalObjectFamily
    role: IdentifierRole
    prefix: str
    regex_pattern: str
    sequence_width: int | None
    example: str
    runtime_scoped: bool = False
    immutable_after_issue: bool = True

    def __post_init__(self) -> None:
        if not self.prefix:
            raise ValueError("identifier prefix is required")
        try:
            compiled = re.compile(self.regex_pattern)
        except re.error as exc:
            raise ValueError("invalid identifier regex") from exc
        if compiled.fullmatch(self.example) is None:
            raise ValueError("identifier example does not satisfy regex")
        if not self.immutable_after_issue:
            raise ValueError("NNGLA canonical identities must remain immutable after issue")
        if self.sequence_width is not None and self.sequence_width < 1:
            raise ValueError("sequence_width must be positive")

    def validates(self, value: str) -> bool:
        return re.fullmatch(self.regex_pattern, str(value)) is not None


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    dataset_id: str
    dataset_version: str
    source_record_id: str
    candidate_id: str | None

    def __post_init__(self) -> None:
        if not self.dataset_id.startswith("dataset:"):
            raise ValueError("dataset_id must use dataset: namespace")
        if not self.dataset_version:
            raise ValueError("dataset_version is required")
        if not self.source_record_id:
            raise ValueError("source_record_id is required")


@dataclass(frozen=True, slots=True)
class CanonicalIdentityProposal:
    source: SourceIdentity
    object_family: CanonicalObjectFamily
    canonical_id: str
    allocation_basis: str

    def __post_init__(self) -> None:
        if not self.canonical_id:
            raise ValueError("canonical_id is required")
        if not self.allocation_basis:
            raise ValueError("allocation_basis is required")


# Bundle 16A introduces canonical namespaces only where earlier locked contracts
# left source/candidate identity as the persistence key. Existing canonical
# namespaces are restated here for audit/validation, not redefined in old files.
CANONICAL_NAMESPACE_CONTRACTS = {
    CanonicalObjectFamily.PLACE: IdentifierNamespaceContract(
        CanonicalObjectFamily.PLACE,
        IdentifierRole.CANONICAL,
        "NG-PLC-",
        r"NG-PLC-\d{6}",
        6,
        "NG-PLC-000001",
    ),
    CanonicalObjectFamily.ADMINISTRATIVE_AREA: IdentifierNamespaceContract(
        CanonicalObjectFamily.ADMINISTRATIVE_AREA,
        IdentifierRole.CANONICAL,
        "NG-ADM-",
        r"NG-ADM-\d{6}",
        6,
        "NG-ADM-000001",
    ),
    CanonicalObjectFamily.ROAD: IdentifierNamespaceContract(
        CanonicalObjectFamily.ROAD,
        IdentifierRole.CANONICAL,
        "NG-RD-",
        r"NG-RD-\d{6}",
        6,
        "NG-RD-000001",
    ),
    CanonicalObjectFamily.GEOGRAPHIC_FEATURE: IdentifierNamespaceContract(
        CanonicalObjectFamily.GEOGRAPHIC_FEATURE,
        IdentifierRole.CANONICAL,
        "NG-FEAT-",
        r"NG-FEAT-\d{6}",
        6,
        "NG-FEAT-000001",
    ),
    CanonicalObjectFamily.GEOMETRY: IdentifierNamespaceContract(
        CanonicalObjectFamily.GEOMETRY,
        IdentifierRole.GEOMETRY,
        "NG-GEO-",
        r"NG-GEO-\d{6}",
        6,
        "NG-GEO-000001",
    ),
    CanonicalObjectFamily.ADDRESS: IdentifierNamespaceContract(
        CanonicalObjectFamily.ADDRESS,
        IdentifierRole.CANONICAL,
        "NG-ADR-",
        r"NG-ADR-\d{6}",
        6,
        "NG-ADR-000001",
    ),
    CanonicalObjectFamily.TITLE: IdentifierNamespaceContract(
        CanonicalObjectFamily.TITLE,
        IdentifierRole.LEGAL,
        "NG-TTL-",
        r"NG-TTL-\d{6}",
        6,
        "NG-TTL-000001",
    ),
}


__all__ = [
    "IdentifierRole",
    "CanonicalObjectFamily",
    "IdentifierNamespaceContract",
    "SourceIdentity",
    "CanonicalIdentityProposal",
    "CANONICAL_NAMESPACE_CONTRACTS",
]
