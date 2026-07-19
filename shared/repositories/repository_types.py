"""
============================================================
Nexa Provider Platform
File: shared/repositories/repository_types.py
Layer: Shared Repository Foundation
Milestone: NPP-M005 — Repository Foundation
============================================================

Defines shared repository enums and type identifiers.

These types provide stable names for repository operations
and repository implementations without coupling higher layers
to a particular storage technology.
"""

from __future__ import annotations

from enum import Enum


class RepositoryOperation(str, Enum):
    """
    Supported repository operations.

    These values are used in repository results, exceptions,
    logging, testing and future audit records.
    """

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    EXISTS = "exists"
    COUNT = "count"


class RepositoryType(str, Enum):
    """
    Supported repository implementation types.

    LOCAL is the Phase 1 implementation backed by the shared
    Storage Foundation.

    Additional implementations such as SUPABASE may be added
    during later roadmap phases without changing Provider
    Services.
    """

    LOCAL = "local"


__all__ = [
    "RepositoryOperation",
    "RepositoryType",
]