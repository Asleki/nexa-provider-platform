"""P006.UI.4/P006.UI.9 — Stable authentication and session contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import FrozenSet


class IdentityType(StrEnum):
    GUEST = "guest"
    NEXADEVS_DEVELOPER = "nexadevs_developer"


class SelectedRuntime(StrEnum):
    PRODUCTION = "production"
    SIMULATION = "simulation"


class AuthenticationStrength(StrEnum):
    GUEST_PASSWORD = "guest_password"
    DEVELOPER_PASSWORD_ENIGMA = "developer_password_enigma"


@dataclass(frozen=True, slots=True)
class Principal:
    principal_id: str
    username: str
    identity_type: IdentityType
    permissions: FrozenSet[str]
    enigma_profile_id: str | None = None


@dataclass(frozen=True, slots=True)
class AuthenticationAttempt:
    attempt_id: str
    principal_id: str
    runtime: SelectedRuntime
    issued_at: str
    expires_at: str
    status: str


@dataclass(frozen=True, slots=True)
class EnigmaChallenge:
    challenge_id: str
    attempt_id: str
    word_length: int
    words: tuple[str, str, str]
    period: str
    issued_at: str
    expires_at: str


@dataclass(frozen=True, slots=True)
class Session:
    session_id: str
    principal_id: str
    username: str
    identity_type: IdentityType
    runtime: SelectedRuntime
    permissions: FrozenSet[str]
    authentication_strength: AuthenticationStrength
    issued_at: str
    expires_at: str
