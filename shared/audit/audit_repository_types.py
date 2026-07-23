"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_repository_types.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.4 — Audit Repository
============================================================

Defines stable audit-repository operation and implementation type
identifiers. Audit repositories are append-only: update, delete and
clear operations are intentionally absent.
"""

from __future__ import annotations

from enum import Enum


class AuditRepositoryOperation(str, Enum):
    """Supported append-only audit-repository operations."""

    APPEND = "append"
    READ = "read"
    LIST = "list"
    EXISTS = "exists"
    COUNT = "count"


class AuditRepositoryType(str, Enum):
    """Supported audit-repository implementation types."""

    MEMORY = "memory"


__all__ = ["AuditRepositoryOperation", "AuditRepositoryType"]
