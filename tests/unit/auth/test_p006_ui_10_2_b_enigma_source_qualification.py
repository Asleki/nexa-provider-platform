from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest

from backend.auth.enigma_catalogue_admission.contracts import (
    EXPECTED_KEYS,
    EXPECTED_ROW_COUNT,
    EnigmaSourceQualificationError,
    EnigmaSourceSpec,
)
from backend.auth.enigma_catalogue_admission.source import (
    EXPECTED_HEADER,
    normalize_lookup_index,
    qualify_source_bytes,
)


def _word(index: int, length: int, salt: int = 0) -> str:
    value = index + salt
    chars = []
    for _ in range(length):
        chars.append(chr(ord("A") + (value % 26)))
        value //= 26
    return "".join(reversed(chars))


def _source_bytes(length: int, *, lookup_prefix: str = "LOOKUP") -> bytes:
    lines = [",".join(EXPECTED_HEADER)]
    index = 0
    for day in range(1, 32):
        for period in ("Morning", "Noon", "Evening"):
            words = (_word(index, length), _word(index, length, 1000), _word(index, length, 2000))
            lines.append(
                f"{day},{period},{words[0]},{words[1]},{words[2]},{lookup_prefix}{index:03d}"
            )
            index += 1
    return ("\n".join(lines) + "\n").encode("ascii")


def _spec(length: int, raw: bytes) -> EnigmaSourceSpec:
    path = Path(f"development/auth/private/enigma/enigma_words_{length}.csv")
    return EnigmaSourceSpec(
        word_length=length,
        relative_path=path,
        source_reference=path.as_posix(),
        expected_sha256=sha256(raw).hexdigest(),
        catalogue_id=f"enigma:catalogue:test:{length}:v1",
    )


def _rehash(length: int, raw: bytes) -> EnigmaSourceSpec:
    return _spec(length, raw)


@pytest.mark.parametrize("length", [3, 4, 5])
def test_strict_source_qualification_proves_complete_93_key_family(length: int) -> None:
    raw = _source_bytes(length)
    result = qualify_source_bytes(_spec(length, raw), raw)

    assert result.row_count == EXPECTED_ROW_COUNT == 93
    assert {row.key for row in result.rows} == EXPECTED_KEYS
    assert result.sha256 == sha256(raw).hexdigest()
    assert result.byte_size == len(raw)
    assert result.encoding == "utf-8"
    assert result.newline_style == "LF"
    assert result.trailing_newline is True
    assert result.metrics.distinct_expected_signatures == 93
    assert result.metrics.expected_signature_collision_groups == 0
    assert result.metrics.expected_signature_collision_occurrences == 0


def test_hash_mismatch_is_rejected_before_source_admission() -> None:
    raw = _source_bytes(3)
    wrong = EnigmaSourceSpec(
        word_length=3,
        relative_path=Path("development/auth/private/enigma/enigma_words_3.csv"),
        source_reference="development/auth/private/enigma/enigma_words_3.csv",
        expected_sha256="0" * 64,
        catalogue_id="enigma:catalogue:test:3:v1",
    )
    with pytest.raises(EnigmaSourceQualificationError, match="hash mismatch"):
        qualify_source_bytes(wrong, raw)


def test_crlf_is_accepted_as_canonical_source_format() -> None:
    base = _source_bytes(3)
    crlf = base.replace(b"\n", b"\r\n")
    result = qualify_source_bytes(_rehash(3, crlf), crlf)

    assert result.row_count == 93
    assert result.newline_style == "CRLF"
    assert result.trailing_newline is True
    assert result.sha256 == sha256(crlf).hexdigest()


def test_bom_mixed_newlines_missing_newline_and_hidden_unicode_are_rejected() -> None:
    base = _source_bytes(3)
    bom = b"\xef\xbb\xbf" + base
    with pytest.raises(EnigmaSourceQualificationError, match="BOM"):
        qualify_source_bytes(_rehash(3, bom), bom)

    crlf = base.replace(b"\n", b"\r\n")
    mixed = crlf.replace(b"\r\n", b"\n", 1)
    with pytest.raises(EnigmaSourceQualificationError, match="mixed LF/CRLF"):
        qualify_source_bytes(_rehash(3, mixed), mixed)

    bare_cr = base.replace(b"\n", b"\r", 1)
    with pytest.raises(EnigmaSourceQualificationError, match="bare carriage return"):
        qualify_source_bytes(_rehash(3, bare_cr), bare_cr)

    no_newline = base[:-1]
    with pytest.raises(EnigmaSourceQualificationError, match="canonical newline"):
        qualify_source_bytes(_rehash(3, no_newline), no_newline)

    hidden = base.replace(b"LOOKUP000", "LOOK\u200bUP000".encode("utf-8"), 1)
    with pytest.raises(EnigmaSourceQualificationError, match="non-ASCII/hidden"):
        qualify_source_bytes(_rehash(3, hidden), hidden)


def test_header_columns_casing_whitespace_and_word_family_drift_are_rejected() -> None:
    base = _source_bytes(4)

    bad_header = base.replace(b"day,time_of_day", b"day,period", 1)
    with pytest.raises(EnigmaSourceQualificationError, match="header"):
        qualify_source_bytes(_rehash(4, bad_header), bad_header)

    extra_column = base.replace(
        b"day,time_of_day,word_1,word_2,word_3,profile_lookup_word\n",
        b"day,time_of_day,word_1,word_2,word_3,profile_lookup_word,extra\n",
        1,
    )
    with pytest.raises(EnigmaSourceQualificationError, match="header"):
        qualify_source_bytes(_rehash(4, extra_column), extra_column)

    bad_period = base.replace(b"1,Morning,", b"1,morning,", 1)
    with pytest.raises(EnigmaSourceQualificationError, match="period"):
        qualify_source_bytes(_rehash(4, bad_period), bad_period)

    bad_word = base.replace(b"1,Morning,AAAA,", b"1,Morning,aaaA,", 1)
    with pytest.raises(EnigmaSourceQualificationError, match="uppercase ASCII"):
        qualify_source_bytes(_rehash(4, bad_word), bad_word)

    lookup_space = base.replace(b"LOOKUP000", b"LOOKUP000 ", 1)
    with pytest.raises(EnigmaSourceQualificationError, match="whitespace"):
        qualify_source_bytes(_rehash(4, lookup_space), lookup_space)


def test_duplicate_and_missing_authority_keys_are_rejected() -> None:
    raw = _source_bytes(3)
    text = raw.decode("ascii").splitlines()
    text[-1] = text[-2]
    duplicate = ("\n".join(text) + "\n").encode("ascii")
    with pytest.raises(EnigmaSourceQualificationError, match="duplicate authority key"):
        qualify_source_bytes(_rehash(3, duplicate), duplicate)

    missing = ("\n".join(raw.decode("ascii").splitlines()[:-1]) + "\n").encode("ascii")
    with pytest.raises(EnigmaSourceQualificationError, match="exactly 93"):
        qualify_source_bytes(_rehash(3, missing), missing)


def test_private_lookup_token_is_not_forced_to_challenge_word_length_and_is_not_exposed() -> None:
    raw = _source_bytes(3, lookup_prefix="PRIVATE_RESPONSE_TOKEN_")
    result = qualify_source_bytes(_spec(3, raw), raw)

    assert all(len(row.words[0]) == 3 for row in result.rows)
    assert "PRIVATE_RESPONSE_TOKEN_" not in repr(result.safe_summary())
    assert not hasattr(result.rows[0], "profile_lookup_word")


def test_repetition_metrics_distinguish_legitimate_material_reuse_from_duplicate_keys() -> None:
    raw = _source_bytes(5)
    lines = raw.decode("ascii").splitlines()
    first = lines[1].split(",")
    second = lines[2].split(",")
    # Reuse challenge triple and lookup token at a different valid day/period key.
    second[2:5] = first[2:5]
    second[5] = first[5]
    lines[2] = ",".join(second)
    changed = ("\n".join(lines) + "\n").encode("ascii")
    result = qualify_source_bytes(_rehash(5, changed), changed)

    assert result.row_count == 93
    assert result.metrics.repeated_challenge_triple_groups == 1
    assert result.metrics.repeated_challenge_triple_occurrences == 1
    assert result.metrics.repeated_lookup_token_groups == 1
    assert result.metrics.repeated_lookup_token_occurrences == 1


def test_lookup_normalization_contract_remains_1_through_31() -> None:
    assert normalize_lookup_index(1) == 1
    assert normalize_lookup_index(31) == 31
    assert normalize_lookup_index(32) == 1
    assert normalize_lookup_index(40) == 9
    with pytest.raises(ValueError):
        normalize_lookup_index(0)
