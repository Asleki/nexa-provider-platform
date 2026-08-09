"""P006.UI.5/P006.UI.8 — Qualified Enigma catalogue and challenge authority."""
from __future__ import annotations

import csv
import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import secrets

from .contracts import AuthenticationAttempt, EnigmaChallenge, Principal

PERIODS = ("Morning", "Noon", "Evening")
CATALOGUE_LENGTHS = (3, 4, 5)
EXPECTED_KEYS = {(day, period) for day in range(1, 32) for period in PERIODS}


class EnigmaCatalogueError(ValueError):
    pass


def period_for_hour(hour: int) -> str:
    if not 0 <= hour <= 23:
        raise ValueError("hour must be between 0 and 23")
    if hour <= 10:
        return "Morning"
    if hour <= 16:
        return "Noon"
    return "Evening"


def normalize_lookup_index(raw_value: int) -> int:
    if raw_value < 1:
        raise ValueError("raw challenge value must be positive")
    return ((raw_value - 1) % 31) + 1


@dataclass(frozen=True, slots=True)
class EnigmaRow:
    day: int
    period: str
    words: tuple[str, str, str]
    profile_lookup_word: str


class EnigmaCatalogue:
    def __init__(self, word_length: int, path: Path):
        if word_length not in CATALOGUE_LENGTHS:
            raise EnigmaCatalogueError("unsupported Enigma word length")
        self.word_length = word_length
        self.path = Path(path)
        self.rows = self._load_and_qualify()

    def _load_and_qualify(self) -> dict[tuple[int, str], EnigmaRow]:
        if not self.path.exists():
            raise EnigmaCatalogueError(f"missing private Enigma catalogue: {self.path}")
        with self.path.open("r", encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle)
            expected_fields = ["day", "time_of_day", "word_1", "word_2", "word_3", "profile_lookup_word"]
            if reader.fieldnames != expected_fields:
                raise EnigmaCatalogueError(f"{self.path} has invalid header")
            rows: dict[tuple[int, str], EnigmaRow] = {}
            for raw in reader:
                try:
                    day = int(raw["day"])
                except (TypeError, ValueError) as exc:
                    raise EnigmaCatalogueError("day must be an integer") from exc
                period = str(raw["time_of_day"]).strip().title()
                words = tuple(str(raw[f"word_{index}"]).strip().upper() for index in range(1, 4))
                lookup = str(raw["profile_lookup_word"]).strip().upper()
                if day not in range(1, 32) or period not in PERIODS:
                    raise EnigmaCatalogueError("invalid day or time period")
                if any(len(word) != self.word_length or not word.isalpha() for word in words):
                    raise EnigmaCatalogueError(
                        f"{self.path.name} contains a word outside the {self.word_length}-letter family"
                    )
                if not lookup or any(ch.isspace() for ch in lookup):
                    raise EnigmaCatalogueError("profile lookup word must be a non-empty token")
                key = (day, period)
                if key in rows:
                    raise EnigmaCatalogueError(f"duplicate Enigma row: {key}")
                rows[key] = EnigmaRow(day, period, words, lookup)
        if set(rows) != EXPECTED_KEYS:
            missing = sorted(EXPECTED_KEYS - set(rows))
            extra = sorted(set(rows) - EXPECTED_KEYS)
            raise EnigmaCatalogueError(f"incomplete Enigma catalogue; missing={missing[:5]} extra={extra[:5]}")
        return rows

    def row(self, day: int, period: str) -> EnigmaRow:
        return self.rows[(day, period)]


class EnigmaAuthority:
    def __init__(self, catalogue_dir: Path):
        catalogue_dir = Path(catalogue_dir)
        self.catalogues = {
            length: EnigmaCatalogue(length, catalogue_dir / f"enigma_words_{length}.csv")
            for length in CATALOGUE_LENGTHS
        }

    @staticmethod
    def select_word_length(attempt_id: str) -> int:
        digest = hashlib.sha256(attempt_id.encode("utf-8")).digest()
        return CATALOGUE_LENGTHS[digest[0] % len(CATALOGUE_LENGTHS)]

    def issue(
        self,
        *,
        attempt: AuthenticationAttempt,
        principal: Principal,
        now: datetime,
        ttl_seconds: int = 180,
    ) -> tuple[EnigmaChallenge, str]:
        if not principal.enigma_profile_id:
            raise EnigmaCatalogueError("developer principal has no Enigma profile")
        length = self.select_word_length(attempt.attempt_id)
        period = period_for_hour(now.hour)
        row = self.catalogues[length].row(now.day, period)
        issued_at = now.astimezone(timezone.utc)
        expires_at = issued_at + timedelta(seconds=ttl_seconds)
        challenge = EnigmaChallenge(
            challenge_id=f"enigma:{secrets.token_urlsafe(18)}",
            attempt_id=attempt.attempt_id,
            word_length=length,
            words=row.words,
            period=period,
            issued_at=issued_at.isoformat(),
            expires_at=expires_at.isoformat(),
        )
        letter_total = sum(len(word) for word in row.words)
        lookup_index = normalize_lookup_index(letter_total + now.day)
        expected_signature = f"{lookup_index}{row.profile_lookup_word}"
        return challenge, expected_signature

    @staticmethod
    def verify(response: str, expected_signature: str) -> bool:
        normalized = "".join(str(response).strip().upper().split())
        return hmac.compare_digest(normalized, expected_signature.upper())
