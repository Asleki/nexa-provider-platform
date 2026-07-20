"""
============================================================
Nexa Provider Platform
File: registries/relationships/relationship_type.py
Layer: Master Registry Foundation
Milestone: NPP-M006.2 — Registry Package Skeleton
============================================================

Defines approved cross-registry relationship types.

Relationships are represented through immutable references.
They do not transfer record ownership and must not create hidden
cross-domain mutation authority.
"""

from __future__ import annotations

from enum import Enum


class RelationshipType(str, Enum):
    """Supported cross-registry relationship types."""

    REFERENCES = "references"
    ISSUED_BY = "issued_by"
    OWNED_BY = "owned_by"
    DERIVED_FROM = "derived_from"
    SUPERSEDES = "supersedes"
    ASSOCIATED_WITH = "associated_with"


__all__ = [
    "RelationshipType",
]
