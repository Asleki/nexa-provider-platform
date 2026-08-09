from datetime import datetime, timezone
from pathlib import Path
import csv
import json

from backend.auth.credentials import hash_password
from backend.auth.development_service import DevelopmentAuthenticationService


PERIODS = ("Morning", "Noon", "Evening")


def _fixtures(root: Path) -> tuple[Path, Path]:
    credentials = root / "credentials"
    enigma = root / "enigma"
    credentials.mkdir()
    enigma.mkdir()

    verifier = hash_password("password-123", salt=b"0123456789abcdef", iterations=1000)
    (credentials / "guests.local.json").write_text(json.dumps([{
        "principalId": "guest:test:0001",
        "username": "guest",
        "identityType": "guest",
        "credentialVerifier": verifier,
        "enabled": True,
        "permissions": ["public:search"],
    }]))
    (credentials / "developers.local.json").write_text(json.dumps([{
        "principalId": "developer:test:0001",
        "username": "developer",
        "identityType": "nexadevs_developer",
        "credentialVerifier": verifier,
        "enabled": True,
        "permissions": ["citizen:view"],
        "enigmaProfileId": "profile:test",
    }]))

    by_length = {
        3: ("CAR", "TAR", "BAR"),
        4: ("CODE", "NODE", "MODE"),
        5: ("STACK", "TRACK", "PACKS"),
    }
    for length, words in by_length.items():
        with (enigma / f"enigma_words_{length}.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["day", "time_of_day", "word_1", "word_2", "word_3", "profile_lookup_word"])
            for day in range(1, 32):
                for period in PERIODS:
                    writer.writerow([day, period, *words, "ARC"])
    return credentials, enigma


def test_guest_and_developer_have_distinct_authentication_strength(tmp_path: Path) -> None:
    credentials, enigma = _fixtures(tmp_path)
    service = DevelopmentAuthenticationService(credential_dir=credentials, catalogue_dir=enigma)

    guest = service.login_guest(username="guest", password="password-123", runtime="production")
    assert guest["identityType"] == "guest"
    assert guest["authenticationStrength"] == "guest_password"

    now = datetime.now(timezone.utc)
    started = service.start_developer(
        username="developer",
        password="password-123",
        runtime="production",
        now=now,
    )
    challenge = started["challenge"]
    # The authority never publishes the lookup word or expected signature.
    assert "profile_lookup_word" not in challenge
    assert "expectedSignature" not in challenge

    raw = sum(len(word) for word in challenge["words"]) + now.day
    lookup_index = ((raw - 1) % 31) + 1
    developer = service.verify_developer(
        attempt_id=started["attemptId"],
        response=f"{lookup_index}ARC",
    )
    assert developer["identityType"] == "nexadevs_developer"
    assert developer["authenticationStrength"] == "developer_password_enigma"
    assert service.session(developer["sessionId"])["principalId"] == "developer:test:0001"
    assert service.logout(developer["sessionId"])
