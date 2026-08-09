"""P006.UI.4 — Private development credential authority."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Iterable

from .contracts import IdentityType, Principal

PBKDF2_ALGORITHM = "sha256"
DEFAULT_ITERATIONS = 210_000


class CredentialAuthorityError(ValueError):
    pass


def hash_password(password: str, *, salt: bytes | None = None, iterations: int = DEFAULT_ITERATIONS) -> str:
    if not isinstance(password, str) or len(password) < 8:
        raise CredentialAuthorityError("development password must contain at least 8 characters")
    salt = salt or os.urandom(16)
    digest = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, iterations)
    return "pbkdf2_sha256${}${}${}".format(
        iterations,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, verifier: str) -> bool:
    try:
        scheme, iteration_text, salt_text, digest_text = verifier.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        iterations = int(iteration_text)
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


class DevelopmentCredentialStore:
    def __init__(self, credential_dir: Path):
        self._credential_dir = Path(credential_dir)
        self._records = self._load_all()

    def _load_all(self) -> dict[str, dict]:
        records: dict[str, dict] = {}
        for filename, expected_type in (
            ("guests.local.json", IdentityType.GUEST),
            ("developers.local.json", IdentityType.NEXADEVS_DEVELOPER),
        ):
            path = self._credential_dir / filename
            if not path.exists():
                raise CredentialAuthorityError(
                    f"missing private development credential fixture: {path}"
                )
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, list):
                raise CredentialAuthorityError(f"{path} must contain a JSON array")
            for record in payload:
                self._validate_record(record, expected_type, path)
                username = record["username"].casefold()
                if username in records:
                    raise CredentialAuthorityError(f"duplicate username: {record['username']}")
                records[username] = record
        return records

    @staticmethod
    def _validate_record(record: dict, expected_type: IdentityType, path: Path) -> None:
        required = {"principalId", "username", "identityType", "credentialVerifier", "enabled", "permissions"}
        if not isinstance(record, dict) or not required.issubset(record):
            raise CredentialAuthorityError(f"malformed credential record in {path}")
        if record["identityType"] != expected_type.value:
            raise CredentialAuthorityError(f"identity type mismatch in {path}")
        if not str(record["principalId"]).strip() or not str(record["username"]).strip():
            raise CredentialAuthorityError(f"blank principal or username in {path}")
        if not isinstance(record["permissions"], list):
            raise CredentialAuthorityError(f"permissions must be a list in {path}")
        if expected_type is IdentityType.NEXADEVS_DEVELOPER and not record.get("enigmaProfileId"):
            raise CredentialAuthorityError("developer requires enigmaProfileId")

    def authenticate(self, username: str, password: str, expected_type: IdentityType) -> Principal | None:
        record = self._records.get(str(username).strip().casefold())
        if not record or not record.get("enabled", False):
            return None
        if record["identityType"] != expected_type.value:
            return None
        if not verify_password(password, record["credentialVerifier"]):
            return None
        return Principal(
            principal_id=record["principalId"],
            username=record["username"],
            identity_type=expected_type,
            permissions=frozenset(str(value) for value in record["permissions"]),
            enigma_profile_id=record.get("enigmaProfileId"),
        )
