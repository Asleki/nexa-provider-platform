"""
============================================================
Nexa Provider Platform
File: shared/audit/audit_action.py
Layer: Shared Audit Infrastructure
Milestone: NPP-M007.1.3 — Audit Action Contract
============================================================

Defines the stable audit action vocabulary used throughout the
Shared Audit Infrastructure.

Audit actions identify the logical operation being audited,
independent of the underlying repository or storage engine.
"""

from __future__ import annotations

from enum import Enum


class AuditAction(str, Enum):
    """Canonical audit actions."""

    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    VALIDATE = "validate"
    PROCESS = "process"
    LOGIN = "login"
    LOGOUT = "logout"
    REGISTER = "register"

    def __str__(self) -> str:
        """Return the serialized enum value."""
        return self.value


__all__ = ["AuditAction"]
