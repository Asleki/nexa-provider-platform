"""P006.7.11.3 reusable NNGLA migration limit contracts.

The limits in this module are qualification guards for migration planning.
They do not replace PostgreSQL CHECK/FK/UNIQUE constraints.  Values are kept
stable and centrally named so later execution adapters do not scatter ad-hoc
length and batch rules across domain code.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re


class LimitKind(str, Enum):
    TEXT_LENGTH = "TEXT_LENGTH"
    NUMERIC_RANGE = "NUMERIC_RANGE"
    BATCH_SIZE = "BATCH_SIZE"
    PAYLOAD_BYTES = "PAYLOAD_BYTES"


@dataclass(frozen=True, slots=True)
class TextLimit:
    code: str
    max_length: int
    allow_blank: bool
    rationale: str
    pattern: str | None = None

    def validate(self, value: object) -> tuple[str, ...]:
        text = "" if value is None else str(value)
        failures: list[str] = []
        if not text and not self.allow_blank:
            failures.append(f"{self.code}:blank")
        if len(text) > self.max_length:
            failures.append(f"{self.code}:too_long:{len(text)}>{self.max_length}")
        if text and self.pattern and re.fullmatch(self.pattern, text) is None:
            failures.append(f"{self.code}:pattern")
        return tuple(failures)


@dataclass(frozen=True, slots=True)
class NumericRange:
    code: str
    minimum: float
    maximum: float
    rationale: str

    def validate(self, value: object) -> tuple[str, ...]:
        try:
            number = float(value)
        except (TypeError, ValueError):
            return (f"{self.code}:not_numeric",)
        if not self.minimum <= number <= self.maximum:
            return (f"{self.code}:range:{number}",)
        return ()


# Existing Name Catalogue/Authority contracts already use 256-character IDs
# and up-to-600-character authority display names.  Bundle 16B adopts those as
# migration guardrails without changing earlier NNGLA schema TEXT columns.
IDENTIFIER_LIMIT = TextLimit(
    "IDENTIFIER",
    256,
    False,
    "Existing canonical-name authority permits identifiers up to 256 characters.",
    r"[^\s]+",
)
NAME_LIMIT = TextLimit(
    "CANONICAL_NAME",
    600,
    False,
    "Existing Name Authority supports composed authority display names up to 600 characters.",
)
CODE_LIMIT = TextLimit(
    "CONTROLLED_CODE",
    128,
    False,
    "Controlled-code guard; current governed NNGLA codes are substantially shorter.",
    r"[A-Za-z0-9][A-Za-z0-9_.:-]*",
)
SOURCE_PATH_LIMIT = TextLimit(
    "SOURCE_PATH",
    2048,
    False,
    "Repository-relative source paths are bounded for safe receipts and audit output.",
)
SOURCE_BASIS_LIMIT = TextLimit(
    "SOURCE_BASIS",
    2000,
    True,
    "Human-readable source/provenance basis remains bounded for audit persistence.",
)
LONGITUDE_RANGE = NumericRange("LONGITUDE", -180.0, 180.0, "Matches PostgreSQL NNGLA longitude CHECK constraint.")
LATITUDE_RANGE = NumericRange("LATITUDE", -90.0, 90.0, "Matches PostgreSQL NNGLA latitude CHECK constraint.")

MIN_BATCH_SIZE = 1
MAX_BATCH_SIZE = 10_000
MAX_SOURCE_PAYLOAD_BYTES = 1_048_576


def validate_batch_limit(limit: int | None) -> tuple[str, ...]:
    if limit is None:
        return ()
    if not isinstance(limit, int):
        return ("BATCH_SIZE:not_integer",)
    if not MIN_BATCH_SIZE <= limit <= MAX_BATCH_SIZE:
        return (f"BATCH_SIZE:range:{limit}",)
    return ()


__all__ = [
    "LimitKind",
    "TextLimit",
    "NumericRange",
    "IDENTIFIER_LIMIT",
    "NAME_LIMIT",
    "CODE_LIMIT",
    "SOURCE_PATH_LIMIT",
    "SOURCE_BASIS_LIMIT",
    "LONGITUDE_RANGE",
    "LATITUDE_RANGE",
    "MIN_BATCH_SIZE",
    "MAX_BATCH_SIZE",
    "MAX_SOURCE_PAYLOAD_BYTES",
    "validate_batch_limit",
]
