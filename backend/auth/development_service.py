"""P006.UI.4-P006.UI.9 — Development authentication orchestration."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from .contracts import AuthenticationStrength, IdentityType, SelectedRuntime
from .credentials import DevelopmentCredentialStore
from .enigma import EnigmaAuthority
from .sessions import DevelopmentSessionStore, utc_now


class AuthenticationRejected(ValueError):
    pass


class DevelopmentAuthenticationService:
    MAX_ENIGMA_ATTEMPTS = 3

    def __init__(self, *, credential_dir: Path, catalogue_dir: Path):
        self.credentials = DevelopmentCredentialStore(credential_dir)
        self.enigma = EnigmaAuthority(catalogue_dir)
        self.sessions = DevelopmentSessionStore()

    @staticmethod
    def _runtime(value: str) -> SelectedRuntime:
        try:
            return SelectedRuntime(str(value).strip().lower())
        except ValueError as exc:
            raise AuthenticationRejected("unsupported runtime") from exc

    @staticmethod
    def _session_payload(session) -> dict:
        return {
            "sessionId": session.session_id,
            "principalId": session.principal_id,
            "username": session.username,
            "identityType": session.identity_type.value,
            "runtime": session.runtime.value,
            "permissions": sorted(session.permissions),
            "authenticationStrength": session.authentication_strength.value,
            "issuedAt": session.issued_at,
            "expiresAt": session.expires_at,
        }

    def login_guest(self, *, username: str, password: str, runtime: str) -> dict:
        selected_runtime = self._runtime(runtime)
        principal = self.credentials.authenticate(username, password, IdentityType.GUEST)
        if not principal:
            raise AuthenticationRejected("invalid credentials")
        session = self.sessions.create_session(
            principal,
            selected_runtime,
            AuthenticationStrength.GUEST_PASSWORD,
        )
        return self._session_payload(session)

    def start_developer(self, *, username: str, password: str, runtime: str, now: datetime | None = None) -> dict:
        selected_runtime = self._runtime(runtime)
        principal = self.credentials.authenticate(username, password, IdentityType.NEXADEVS_DEVELOPER)
        if not principal:
            raise AuthenticationRejected("invalid credentials")
        attempt = self.sessions.create_attempt(principal, selected_runtime)
        current = now or utc_now()
        challenge, expected = self.enigma.issue(
            attempt=attempt,
            principal=principal,
            now=current,
        )
        self.sessions.bind_challenge(attempt.attempt_id, challenge, expected)
        return {
            "attemptId": attempt.attempt_id,
            "challenge": {
                "challengeId": challenge.challenge_id,
                "wordLength": challenge.word_length,
                "words": list(challenge.words),
                "period": challenge.period,
                "issuedAt": challenge.issued_at,
                "expiresAt": challenge.expires_at,
            },
        }

    def verify_developer(self, *, attempt_id: str, response: str) -> dict:
        record = self.sessions.attempt_record(attempt_id)
        if not record:
            raise AuthenticationRejected("authentication attempt is unavailable")
        challenge = record["challenge"]
        if not challenge or not record["expected_signature"]:
            raise AuthenticationRejected("Enigma challenge is unavailable")
        if datetime.fromisoformat(challenge.expires_at) <= utc_now():
            self.sessions.consume_attempt(attempt_id)
            raise AuthenticationRejected("Enigma challenge expired")
        attempts = self.sessions.increment_challenge_attempts(attempt_id)
        if attempts > self.MAX_ENIGMA_ATTEMPTS:
            self.sessions.consume_attempt(attempt_id)
            raise AuthenticationRejected("Enigma attempt limit exceeded")
        if not self.enigma.verify(response, record["expected_signature"]):
            if attempts >= self.MAX_ENIGMA_ATTEMPTS:
                self.sessions.consume_attempt(attempt_id)
            raise AuthenticationRejected("invalid Enigma response")
        attempt = record["attempt"]
        principal = record["principal"]
        session = self.sessions.create_session(
            principal,
            attempt.runtime,
            AuthenticationStrength.DEVELOPER_PASSWORD_ENIGMA,
        )
        self.sessions.consume_attempt(attempt_id)
        return self._session_payload(session)

    def session(self, session_id: str) -> dict:
        session = self.sessions.get_session(session_id)
        if not session:
            raise AuthenticationRejected("session unavailable")
        return self._session_payload(session)

    def logout(self, session_id: str) -> bool:
        return self.sessions.revoke_session(session_id)
