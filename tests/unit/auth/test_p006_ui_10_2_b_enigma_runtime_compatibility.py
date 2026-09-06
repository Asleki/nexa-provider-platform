from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path

import pytest

from backend.auth.contracts import AuthenticationAttempt, IdentityType, Principal, SelectedRuntime
from backend.auth.credentials import hash_password
from backend.auth.development_service import AuthenticationRejected, DevelopmentAuthenticationService
from backend.auth.enigma import EnigmaAuthority, normalize_lookup_index, period_for_hour


def _word(index: int, length: int, salt: int = 0) -> str:
    value = index + salt
    chars = []
    for _ in range(length):
        chars.append(chr(ord("A") + value % 26))
        value //= 26
    return "".join(reversed(chars))


def _write_catalogues(directory: Path, lookup_token: str = "LOOKUP") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for length in (3, 4, 5):
        lines = ["day,time_of_day,word_1,word_2,word_3,profile_lookup_word"]
        index = 0
        for day in range(1, 32):
            for period in ("Morning", "Noon", "Evening"):
                words = (_word(index, length), _word(index, length, 1000), _word(index, length, 2000))
                lines.append(f"{day},{period},{words[0]},{words[1]},{words[2]},{lookup_token}")
                index += 1
        (directory / f"enigma_words_{length}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_credentials(directory: Path, password: str = "Developer-Test-Password!") -> None:
    directory.mkdir(parents=True, exist_ok=True)
    verifier = hash_password(password, salt=b"0123456789abcdef", iterations=1000)
    (directory / "guests.local.json").write_text("[]\n", encoding="utf-8")
    (directory / "developers.local.json").write_text(
        json.dumps(
            [
                {
                    "principalId": "developer:test:001",
                    "username": "developer_test",
                    "identityType": "nexadevs_developer",
                    "credentialVerifier": verifier,
                    "enigmaProfileId": "enigma:profile:test:v1",
                    "enabled": True,
                    "permissions": ["registry:view"],
                }
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_sha256_attempt_id_selection_is_deterministic_for_all_three_families() -> None:
    observed = {}
    for index in range(10_000):
        attempt_id = f"auth:test:{index}"
        digest = sha256(attempt_id.encode("utf-8")).digest()
        expected = (3, 4, 5)[digest[0] % 3]
        actual = EnigmaAuthority.select_word_length(attempt_id)
        assert actual == expected
        observed.setdefault(actual, attempt_id)
        if set(observed) == {3, 4, 5}:
            break
    assert set(observed) == {3, 4, 5}


def test_period_boundaries_and_lookup_normalization_are_frozen() -> None:
    assert period_for_hour(0) == "Morning"
    assert period_for_hour(10) == "Morning"
    assert period_for_hour(11) == "Noon"
    assert period_for_hour(16) == "Noon"
    assert period_for_hour(17) == "Evening"
    assert period_for_hour(23) == "Evening"
    assert normalize_lookup_index(31) == 31
    assert normalize_lookup_index(32) == 1
    assert normalize_lookup_index(40) == 9


def test_controlled_3_4_5_letter_examples_preserve_signature_shape_and_expiry(tmp_path: Path) -> None:
    catalogue_dir = tmp_path / "enigma"
    _write_catalogues(catalogue_dir, lookup_token="PRIVATE_TEST_TOKEN")
    authority = EnigmaAuthority(catalogue_dir)
    principal = Principal(
        "developer:test:001",
        "developer_test",
        IdentityType.NEXADEVS_DEVELOPER,
        frozenset({"registry:view"}),
        "enigma:profile:test:v1",
    )
    now = datetime(2026, 9, 6, 12, 30, tzinfo=timezone.utc)

    selected = {}
    for index in range(10_000):
        attempt_id = f"auth:controlled:{index}"
        length = authority.select_word_length(attempt_id)
        if length in selected:
            continue
        attempt = AuthenticationAttempt(
            attempt_id,
            principal.principal_id,
            SelectedRuntime.PRODUCTION,
            now.isoformat(),
            (now + timedelta(seconds=300)).isoformat(),
            "primary_verified",
        )
        challenge, expected = authority.issue(attempt=attempt, principal=principal, now=now)
        assert challenge.word_length == length
        assert challenge.period == "Noon"
        assert datetime.fromisoformat(challenge.expires_at) - datetime.fromisoformat(challenge.issued_at) == timedelta(seconds=180)
        assert expected == f"{normalize_lookup_index(now.day + (3 * length))}PRIVATE_TEST_TOKEN"
        selected[length] = expected
        if set(selected) == {3, 4, 5}:
            break

    assert set(selected) == {3, 4, 5}


def test_response_normalization_and_constant_time_compare_behavior_are_compatible() -> None:
    expected = "18PRIVATE_TOKEN"
    assert EnigmaAuthority.verify(" 18 private_token ", expected)
    assert EnigmaAuthority.verify("18\nPRIVATE_TOKEN", expected)
    assert not EnigmaAuthority.verify("19PRIVATE_TOKEN", expected)


def test_development_service_preserves_three_attempt_limit_and_success_strength(tmp_path: Path, monkeypatch) -> None:
    credentials = tmp_path / "credentials"
    catalogues = tmp_path / "enigma"
    _write_credentials(credentials)
    _write_catalogues(catalogues, lookup_token="LOOKUP")
    fixed_now = datetime(2026, 9, 6, 12, 30, tzinfo=timezone.utc)
    monkeypatch.setattr("backend.auth.development_service.utc_now", lambda: fixed_now)

    service = DevelopmentAuthenticationService(credential_dir=credentials, catalogue_dir=catalogues)
    started = service.start_developer(
        username="developer_test",
        password="Developer-Test-Password!",
        runtime="production",
        now=fixed_now,
    )
    attempt_id = started["attemptId"]
    for _ in range(3):
        with pytest.raises(AuthenticationRejected, match="invalid Enigma response"):
            service.verify_developer(attempt_id=attempt_id, response="WRONG")
    with pytest.raises(AuthenticationRejected, match="unavailable"):
        service.verify_developer(attempt_id=attempt_id, response="WRONG")

    started = service.start_developer(
        username="developer_test",
        password="Developer-Test-Password!",
        runtime="production",
        now=fixed_now,
    )
    length = started["challenge"]["wordLength"]
    expected = f"{normalize_lookup_index(fixed_now.day + 3 * length)}LOOKUP"
    session = service.verify_developer(attempt_id=started["attemptId"], response=f" {expected.lower()} ")
    assert session["authenticationStrength"] == "developer_password_enigma"
