"""
============================================================
Nexa Provider Platform
File: registries/validators/registry_validation_checklist.py
Layer: Master Registry Foundation
Milestone: NPP-M008.9 — Registry Validation
============================================================

Stable, side-effect-free checklist describing the definition fields
covered by Registry Validation.
============================================================
"""
from __future__ import annotations
from typing import Final

REGISTRY_VALIDATION_CHECKLIST: Final[tuple[str, ...]] = (
    "registry_id",
    "registry_code",
    "registry_name",
    "family",
    "status",
    "description",
    "version",
    "metadata",
)

def registry_validation_checklist() -> tuple[str, ...]:
    """Return the immutable ordered registry-definition checklist."""
    return REGISTRY_VALIDATION_CHECKLIST

__all__ = ("REGISTRY_VALIDATION_CHECKLIST", "registry_validation_checklist")
