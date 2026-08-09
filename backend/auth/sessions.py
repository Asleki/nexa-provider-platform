"""P006.UI.9 — In-memory development authentication attempts and sessions."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import secrets
from threading import RLock

from .contracts import (
    AuthenticationAttempt,
    AuthenticationStrength,
    IdentityType,
    Principal,
    SelectedRuntime,
    Session,
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class DevelopmentSessionStore:
    def __init__(self):
        self._lock = RLock()
        self._attempts: dict[str, dict] = {}
        self._sessions: dict[str, Session] = {}

    def create_attempt(self, principal: Principal, runtime: SelectedRuntime, *, ttl_seconds: int = 300) -> AuthenticationAttempt:
        now = utc_now()
        attempt = AuthenticationAttempt(
            attempt_id=f"auth:{secrets.token_urlsafe(18)}",
            principal_id=principal.principal_id,
            runtime=runtime,
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat(),
            status="primary_verified",
        )
        with self._lock:
            self._attempts[attempt.attempt_id] = {
                "attempt": attempt,
                "principal": principal,
                "challenge": None,
                "expected_signature": None,
                "challenge_attempts": 0,
            }
        return attempt

    def bind_challenge(self, attempt_id: str, challenge, expected_signature: str) -> None:
        with self._lock:
            record = self._attempts[attempt_id]
            record["challenge"] = challenge
            record["expected_signature"] = expected_signature

    def attempt_record(self, attempt_id: str) -> dict | None:
        with self._lock:
            record = self._attempts.get(attempt_id)
            return dict(record) if record else None

    def increment_challenge_attempts(self, attempt_id: str) -> int:
        with self._lock:
            record = self._attempts[attempt_id]
            record["challenge_attempts"] += 1
            return record["challenge_attempts"]

    def consume_attempt(self, attempt_id: str) -> None:
        with self._lock:
            self._attempts.pop(attempt_id, None)

    def create_session(
        self,
        principal: Principal,
        runtime: SelectedRuntime,
        strength: AuthenticationStrength,
        *,
        ttl_seconds: int = 3600,
    ) -> Session:
        now = utc_now()
        session = Session(
            session_id=f"session:{secrets.token_urlsafe(24)}",
            principal_id=principal.principal_id,
            username=principal.username,
            identity_type=principal.identity_type,
            runtime=runtime,
            permissions=principal.permissions,
            authentication_strength=strength,
            issued_at=now.isoformat(),
            expires_at=(now + timedelta(seconds=ttl_seconds)).isoformat(),
        )
        with self._lock:
            self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Session | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            if datetime.fromisoformat(session.expires_at) <= utc_now():
                self._sessions.pop(session_id, None)
                return None
            return session

    def revoke_session(self, session_id: str) -> bool:
        with self._lock:
            return self._sessions.pop(session_id, None) is not None
