from datetime import datetime, timezone
from pathlib import Path
import csv

import pytest

from backend.auth.contracts import AuthenticationAttempt, IdentityType, Principal, SelectedRuntime
from backend.auth.enigma import EnigmaAuthority, EnigmaCatalogue, EnigmaCatalogueError, normalize_lookup_index, period_for_hour


PERIODS = ("Morning", "Noon", "Evening")


def _catalogue(path: Path, length: int) -> None:
    words = {
        3: ("CAR", "TAR", "BAR"),
        4: ("CODE", "NODE", "MODE"),
        5: ("STACK", "TRACK", "PACKS"),
    }[length]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["day", "time_of_day", "word_1", "word_2", "word_3", "profile_lookup_word"])
        for day in range(1, 32):
            for period in PERIODS:
                writer.writerow([day, period, *words, "ARC"])


def test_catalogue_requires_all_93_day_period_rows(tmp_path: Path) -> None:
    path = tmp_path / "enigma_words_3.csv"
    _catalogue(path, 3)
    catalogue = EnigmaCatalogue(3, path)
    assert len(catalogue.rows) == 93

    rows = path.read_text().splitlines()
    path.write_text("\n".join(rows[:-1]) + "\n")
    with pytest.raises(EnigmaCatalogueError):
        EnigmaCatalogue(3, path)


def test_enigma_period_and_signature_are_deterministic(tmp_path: Path) -> None:
    for length in (3, 4, 5):
        _catalogue(tmp_path / f"enigma_words_{length}.csv", length)
    authority = EnigmaAuthority(tmp_path)
    principal = Principal(
        "developer:test:0001",
        "developer",
        IdentityType.NEXADEVS_DEVELOPER,
        frozenset({"registry:view"}),
        "profile:test",
    )
    attempt = AuthenticationAttempt(
        "auth:fixed",
        principal.principal_id,
        SelectedRuntime.PRODUCTION,
        "2026-08-09T08:00:00+00:00",
        "2026-08-09T08:05:00+00:00",
        "primary_verified",
    )
    now = datetime(2026, 8, 9, 8, 0, tzinfo=timezone.utc)
    challenge, signature = authority.issue(attempt=attempt, principal=principal, now=now)
    assert challenge.period == "Morning"
    assert challenge.words
    expected_index = normalize_lookup_index(sum(len(word) for word in challenge.words) + 9)
    assert signature == f"{expected_index}ARC"
    assert authority.verify(signature.lower(), signature)
    assert period_for_hour(11) == "Noon"
    assert period_for_hour(17) == "Evening"
