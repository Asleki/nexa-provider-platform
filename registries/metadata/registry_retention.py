"""Immutable registry-level retention policy declaration."""
from __future__ import annotations
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from types import MappingProxyType
from .registry_retention_mode import RegistryRetentionMode
from .registry_metadata_errors import RegistryRetentionError

def _dt(value, name):
    if value is None: return None
    if not isinstance(value, datetime): raise TypeError(f"{name} must be a datetime or None.")
    if value.tzinfo is None or value.utcoffset() is None: raise RegistryRetentionError(f"{name} must be timezone-aware.")
    return value.astimezone(timezone.utc)

@dataclass(frozen=True, slots=True)
class RegistryRetention:
    mode: RegistryRetentionMode
    reason: str
    retention_period: timedelta | None = None
    retain_until: datetime | None = None
    trigger_event: str = ""
    archive_required: bool = False
    deletion_permitted: bool = False
    legal_hold: bool = False
    review_at: datetime | None = None
    policy_reference: str = ""
    version: int = 1
    attributes: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self):
        object.__setattr__(self, "mode", RegistryRetentionMode.from_value(self.mode))
        for name in ("reason", "trigger_event", "policy_reference"):
            value = getattr(self, name)
            if not isinstance(value, str): raise TypeError(f"{name} must be text.")
            value = value.strip()
            if name == "reason" and not value: raise RegistryRetentionError("reason cannot be empty.")
            object.__setattr__(self, name, value)
        for name in ("archive_required", "deletion_permitted", "legal_hold"):
            if not isinstance(getattr(self, name), bool): raise TypeError(f"{name} must be a boolean.")
        if self.retention_period is not None and not isinstance(self.retention_period, timedelta): raise TypeError("retention_period must be a timedelta or None.")
        if self.retention_period is not None and self.retention_period <= timedelta(0): raise RegistryRetentionError("retention_period must be positive.")
        object.__setattr__(self, "retain_until", _dt(self.retain_until, "retain_until"))
        object.__setattr__(self, "review_at", _dt(self.review_at, "review_at"))
        if self.mode is RegistryRetentionMode.FIXED_DURATION and self.retention_period is None: raise RegistryRetentionError("FIXED_DURATION requires retention_period.")
        if self.mode is RegistryRetentionMode.UNTIL_DATE and self.retain_until is None: raise RegistryRetentionError("UNTIL_DATE requires retain_until.")
        if self.mode is RegistryRetentionMode.EVENT_TRIGGERED and not self.trigger_event: raise RegistryRetentionError("EVENT_TRIGGERED requires trigger_event.")
        if self.mode is RegistryRetentionMode.LEGAL_HOLD and not self.legal_hold: raise RegistryRetentionError("LEGAL_HOLD requires legal_hold=True.")
        if self.mode is RegistryRetentionMode.PERMANENT and self.deletion_permitted: raise RegistryRetentionError("PERMANENT retention cannot permit deletion.")
        if self.legal_hold and self.deletion_permitted: raise RegistryRetentionError("legal hold cannot permit deletion.")
        if isinstance(self.version, bool) or not isinstance(self.version, int): raise TypeError("version must be an integer.")
        if self.version < 1: raise RegistryRetentionError("version must be at least 1.")
        if not isinstance(self.attributes, Mapping): raise TypeError("attributes must be a mapping.")
        object.__setattr__(self, "attributes", MappingProxyType(dict(self.attributes)))

    def to_dict(self):
        return {"mode": self.mode.value, "reason": self.reason,
                "retention_seconds": None if self.retention_period is None else int(self.retention_period.total_seconds()),
                "retain_until": None if self.retain_until is None else self.retain_until.isoformat(),
                "trigger_event": self.trigger_event, "archive_required": self.archive_required,
                "deletion_permitted": self.deletion_permitted, "legal_hold": self.legal_hold,
                "review_at": None if self.review_at is None else self.review_at.isoformat(),
                "policy_reference": self.policy_reference, "version": self.version,
                "attributes": dict(self.attributes)}
__all__ = ["RegistryRetention"]
