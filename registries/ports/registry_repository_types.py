"""
============================================================
Nexa Provider Platform
File: registries/ports/registry_repository_types.py
Layer: Master Registry Foundation
Milestone: NPP-M008.4 — Registry Repository Interface
============================================================

Stable, storage-neutral operation identifiers used by registry
repository ports, results, errors, tests, and later audit integration.
============================================================
"""

from __future__ import annotations

from enum import Enum


class RegistryRepositoryOperation(str, Enum):
    """Operations supported by the registry repository boundary."""

    ADD = "add"
    READ = "read"
    REPLACE = "replace"
    REMOVE = "remove"
    LIST = "list"
    EXISTS = "exists"
    COUNT = "count"
    CLEAR = "clear"


__all__ = ["RegistryRepositoryOperation"]
