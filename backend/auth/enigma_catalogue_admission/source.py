"""P006.UI.10.2.B — Strict private-source qualification for governed Enigma catalogues.

This module deliberately does not normalize malformed source data. The locked
Development Enigma loader remains permissive for local fixtures; governed
admission rejects drift and anomalies instead of repairing them.
"""
from __future__ import annotations

from collections import Counter
import codecs
import csv
from hashlib import sha256
import io
from pathlib import Path
import re
from typing import Iterable

from .contracts import (
    EXPECTED_KEYS,
    EXPECTED_ROW_COUNT,
    PERIODS,
    WORD_LENGTHS,
    EnigmaRepetitionMetrics,
    EnigmaSourceQualificationError,
    EnigmaSourceSpec,
    QualifiedEnigmaRow,
    QualifiedEnigmaSource,
)


EXPECTED_HEADER = (
    "day",
    "time_of_day",
    "word_1",
    "word_2",
    "word_3",
    "profile_lookup_word",
)
_DAY_PATTERN = re.compile(r"^(?:[1-9]|[12][0-9]|3[01])$")
_ASCII_VISIBLE_MIN = 0x21
_ASCII_VISIBLE_MAX = 0x7E


DEFAULT_SOURCE_SPECS = (
    EnigmaSourceSpec(
        word_length=3,
        relative_path=Path("development/auth/private/enigma/enigma_words_3.csv"),
        source_reference="development/auth/private/enigma/enigma_words_3.csv",
        expected_sha256="aff0a9324d273dfe5c67c9c05421308b250e56b59c5bbeb1faa1fc8764e16fa8",
        catalogue_id="enigma:catalogue:shared:3:v1",
    ),
    EnigmaSourceSpec(
        word_length=4,
        relative_path=Path("development/auth/private/enigma/enigma_words_4.csv"),
        source_reference="development/auth/private/enigma/enigma_words_4.csv",
        expected_sha256="481c59c836e84d797b5cd1c1633618551d8329575be542c8f426a14e088dc1a0",
        catalogue_id="enigma:catalogue:shared:4:v1",
    ),
    EnigmaSourceSpec(
        word_length=5,
        relative_path=Path("development/auth/private/enigma/enigma_words_5.csv"),
        source_reference="development/auth/private/enigma/enigma_words_5.csv",
        expected_sha256="ca003d38352b5b6f348000608cf7b0a6f70f8e42557735b85aaaa2d8b981fa9e",
        catalogue_id="enigma:catalogue:shared:5:v1",
    ),
)


def normalize_lookup_index(raw_value: int) -> int:
    """Mirror the locked P006.UI.5/P006.UI.8 Enigma 1..31 normalization."""
    if raw_value < 1:
        raise ValueError("raw challenge value must be positive")
    return ((raw_value - 1) % 31) + 1


def _duplicate_metrics(counter: Counter[object]) -> tuple[int, int]:
    repeated = [count for count in counter.values() if count > 1]
    return len(repeated), sum(count - 1 for count in repeated)


def _ensure_ascii_source(text: str) -> None:
    for index, character in enumerate(text):
        if character in {"\r", "\n"}:
            continue
        codepoint = ord(character)
        if codepoint < 0x20 or codepoint > 0x7E:
            raise EnigmaSourceQualificationError(
                f"source contains a non-ASCII/hidden character at character offset {index}"
            )


def _qualify_lookup_token(value: str, *, row_number: int) -> None:
    if not value:
        raise EnigmaSourceQualificationError(
            f"row {row_number}: profile_lookup_word is blank"
        )
    if value != value.strip() or any(character.isspace() for character in value):
        raise EnigmaSourceQualificationError(
            f"row {row_number}: profile_lookup_word contains whitespace"
        )
    if any(not (_ASCII_VISIBLE_MIN <= ord(character) <= _ASCII_VISIBLE_MAX) for character in value):
        raise EnigmaSourceQualificationError(
            f"row {row_number}: profile_lookup_word contains a hidden/non-ASCII character"
        )


def qualify_source_bytes(spec: EnigmaSourceSpec, raw_bytes: bytes) -> QualifiedEnigmaSource:
    if not isinstance(raw_bytes, (bytes, bytearray)):
        raise TypeError("raw_bytes must be bytes")
    source_bytes = bytes(raw_bytes)
    actual_sha256 = sha256(source_bytes).hexdigest()
    if actual_sha256 != spec.expected_sha256:
        raise EnigmaSourceQualificationError(
            f"source hash mismatch for {spec.source_reference}; admission refuses drift"
        )
    if source_bytes.startswith(codecs.BOM_UTF8):
        raise EnigmaSourceQualificationError(
            f"source contains a UTF-8 BOM: {spec.source_reference}"
        )
    try:
        text = source_bytes.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise EnigmaSourceQualificationError(
            f"source is not strict UTF-8: {spec.source_reference}"
        ) from exc
    crlf_count = text.count("\r\n")
    lf_count = text.count("\n")
    without_crlf = text.replace("\r\n", "")
    if "\r" in without_crlf:
        raise EnigmaSourceQualificationError(
            f"source contains a bare carriage return: {spec.source_reference}"
        )
    if crlf_count and lf_count != crlf_count:
        raise EnigmaSourceQualificationError(
            f"source contains mixed LF/CRLF newline styles: {spec.source_reference}"
        )
    newline_style = "CRLF" if crlf_count else "LF"
    terminal_newline = "\r\n" if newline_style == "CRLF" else "\n"
    if not text.endswith(terminal_newline):
        raise EnigmaSourceQualificationError(
            f"source must end with one canonical newline: {spec.source_reference}"
        )
    if text.endswith(terminal_newline + terminal_newline):
        raise EnigmaSourceQualificationError(
            f"source contains an unexpected trailing blank line: {spec.source_reference}"
        )
    _ensure_ascii_source(text)

    reader = csv.reader(io.StringIO(text, newline=""), strict=True)
    try:
        header = tuple(next(reader))
    except StopIteration as exc:
        raise EnigmaSourceQualificationError("source is empty") from exc
    except csv.Error as exc:
        raise EnigmaSourceQualificationError("source CSV header is malformed") from exc
    if header != EXPECTED_HEADER:
        raise EnigmaSourceQualificationError(
            f"source header must be exactly {','.join(EXPECTED_HEADER)}"
        )

    seen_keys: set[tuple[int, str]] = set()
    shared_rows: list[QualifiedEnigmaRow] = []
    challenge_triples: Counter[tuple[str, str, str]] = Counter()
    lookup_tokens: Counter[str] = Counter()
    expected_signatures: Counter[str] = Counter()

    try:
        for csv_row_number, row in enumerate(reader, start=2):
            if len(row) != len(EXPECTED_HEADER):
                raise EnigmaSourceQualificationError(
                    f"row {csv_row_number}: expected exactly {len(EXPECTED_HEADER)} columns"
                )
            day_text, period, word_1, word_2, word_3, lookup_token = row
            if not _DAY_PATTERN.fullmatch(day_text):
                raise EnigmaSourceQualificationError(
                    f"row {csv_row_number}: day must be canonical 1..31"
                )
            day = int(day_text)
            if period not in PERIODS:
                raise EnigmaSourceQualificationError(
                    f"row {csv_row_number}: period must be Morning, Noon or Evening"
                )
            words = (word_1, word_2, word_3)
            pattern = re.compile(rf"^[A-Z]{{{spec.word_length}}}$")
            for position, word in enumerate(words, start=1):
                if not pattern.fullmatch(word):
                    raise EnigmaSourceQualificationError(
                        f"row {csv_row_number}: word_{position} must be exactly "
                        f"{spec.word_length} uppercase ASCII letters"
                    )
            _qualify_lookup_token(lookup_token, row_number=csv_row_number)

            key = (day, period)
            if key in seen_keys:
                raise EnigmaSourceQualificationError(
                    f"row {csv_row_number}: duplicate authority key day={day} period={period}"
                )
            seen_keys.add(key)
            shared_rows.append(QualifiedEnigmaRow(day, period, words))
            challenge_triples[words] += 1
            lookup_tokens[lookup_token] += 1

            letter_total = sum(len(word) for word in words)
            lookup_index = normalize_lookup_index(letter_total + day)
            expected_signatures[f"{lookup_index}{lookup_token.upper()}"] += 1
    except csv.Error as exc:
        raise EnigmaSourceQualificationError("source CSV body is malformed") from exc

    if len(shared_rows) != EXPECTED_ROW_COUNT:
        raise EnigmaSourceQualificationError(
            f"source must contain exactly {EXPECTED_ROW_COUNT} data rows"
        )
    if seen_keys != EXPECTED_KEYS:
        missing = sorted(EXPECTED_KEYS - seen_keys)
        extra = sorted(seen_keys - EXPECTED_KEYS)
        raise EnigmaSourceQualificationError(
            f"source day/period coverage is incomplete; missing={missing[:5]} extra={extra[:5]}"
        )

    repeated_triple_groups, repeated_triple_occurrences = _duplicate_metrics(challenge_triples)
    repeated_lookup_groups, repeated_lookup_occurrences = _duplicate_metrics(lookup_tokens)
    signature_collision_groups, signature_collision_occurrences = _duplicate_metrics(expected_signatures)

    shared_rows.sort(key=lambda item: (item.day_of_month, PERIODS.index(item.period)))
    return QualifiedEnigmaSource(
        spec=spec,
        byte_size=len(source_bytes),
        sha256=actual_sha256,
        encoding="utf-8",
        newline_style=newline_style,
        trailing_newline=True,
        row_count=len(shared_rows),
        rows=tuple(shared_rows),
        metrics=EnigmaRepetitionMetrics(
            distinct_challenge_triples=len(challenge_triples),
            repeated_challenge_triple_groups=repeated_triple_groups,
            repeated_challenge_triple_occurrences=repeated_triple_occurrences,
            distinct_lookup_tokens=len(lookup_tokens),
            repeated_lookup_token_groups=repeated_lookup_groups,
            repeated_lookup_token_occurrences=repeated_lookup_occurrences,
            distinct_expected_signatures=len(expected_signatures),
            expected_signature_collision_groups=signature_collision_groups,
            expected_signature_collision_occurrences=signature_collision_occurrences,
        ),
    )


def qualify_source_file(repository_root: Path, spec: EnigmaSourceSpec) -> QualifiedEnigmaSource:
    path = spec.resolve(repository_root)
    if not path.is_file():
        raise EnigmaSourceQualificationError(
            f"missing private Enigma source: {spec.source_reference}"
        )
    return qualify_source_bytes(spec, path.read_bytes())


def qualify_all_sources(
    repository_root: Path,
    specs: Iterable[EnigmaSourceSpec] = DEFAULT_SOURCE_SPECS,
) -> tuple[QualifiedEnigmaSource, ...]:
    ordered_specs = tuple(specs)
    if tuple(spec.word_length for spec in ordered_specs) != WORD_LENGTHS:
        raise EnigmaSourceQualificationError(
            "governed admission requires exactly the 3-, 4- and 5-letter source families"
        )
    qualified = tuple(qualify_source_file(repository_root, spec) for spec in ordered_specs)
    if sum(source.row_count for source in qualified) != EXPECTED_ROW_COUNT * len(WORD_LENGTHS):
        raise EnigmaSourceQualificationError("qualified source total is not exactly 279 rows")
    return qualified


__all__ = [
    "DEFAULT_SOURCE_SPECS",
    "EXPECTED_HEADER",
    "normalize_lookup_index",
    "qualify_all_sources",
    "qualify_source_bytes",
    "qualify_source_file",
]
