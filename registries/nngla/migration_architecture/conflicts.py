"""P006.7.11.2 canonical conflict and quarantine decision contracts."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from collections.abc import Mapping


class ConflictCode(str, Enum):
    ALREADY_EXISTING = "ALREADY_EXISTING"
    IDEMPOTENT_REUSE = "IDEMPOTENT_REUSE"
    ALREADY_CANONICALIZED = "ALREADY_CANONICALIZED"
    SOURCE_ID_CONFLICT = "SOURCE_ID_CONFLICT"
    CANONICAL_ID_CONFLICT = "CANONICAL_ID_CONFLICT"
    CROSSWALK_CONFLICT = "CROSSWALK_CONFLICT"
    NAME_COLLISION = "NAME_COLLISION"
    REFERENCE_CONFLICT = "REFERENCE_CONFLICT"
    COORDINATE_INVALID = "COORDINATE_INVALID"
    BOUNDARY_CONFLICT = "BOUNDARY_CONFLICT"


class ConflictDisposition(str, Enum):
    REUSE = "REUSE"
    REVIEW = "REVIEW"
    QUARANTINE = "QUARANTINE"
    BLOCK = "BLOCK"


_DEFAULT_DISPOSITION = {
    ConflictCode.ALREADY_EXISTING: ConflictDisposition.REUSE,
    ConflictCode.IDEMPOTENT_REUSE: ConflictDisposition.REUSE,
    ConflictCode.ALREADY_CANONICALIZED: ConflictDisposition.REUSE,
    ConflictCode.SOURCE_ID_CONFLICT: ConflictDisposition.QUARANTINE,
    ConflictCode.CANONICAL_ID_CONFLICT: ConflictDisposition.BLOCK,
    ConflictCode.CROSSWALK_CONFLICT: ConflictDisposition.BLOCK,
    ConflictCode.NAME_COLLISION: ConflictDisposition.REVIEW,
    ConflictCode.REFERENCE_CONFLICT: ConflictDisposition.QUARANTINE,
    ConflictCode.COORDINATE_INVALID: ConflictDisposition.QUARANTINE,
    ConflictCode.BOUNDARY_CONFLICT: ConflictDisposition.QUARANTINE,
}


@dataclass(frozen=True, slots=True)
class ConflictFinding:
    code: ConflictCode
    subject_id: str
    disposition: ConflictDisposition
    detail: str

    @classmethod
    def create(cls, code: ConflictCode, subject_id: str, detail: str) -> "ConflictFinding":
        return cls(code, subject_id, _DEFAULT_DISPOSITION[code], detail)


@dataclass(frozen=True, slots=True)
class ExistingCrosswalk:
    source_record_id: str
    canonical_id: str
    canonical_version: int
    source_payload_sha256: str


@dataclass(frozen=True, slots=True)
class ConflictDecision:
    findings: tuple[ConflictFinding, ...]

    @property
    def blocks_execution(self) -> bool:
        return any(f.disposition is ConflictDisposition.BLOCK for f in self.findings)

    @property
    def requires_quarantine(self) -> bool:
        return any(f.disposition is ConflictDisposition.QUARANTINE for f in self.findings)

    @property
    def reusable(self) -> bool:
        return bool(self.findings) and all(f.disposition is ConflictDisposition.REUSE for f in self.findings)


class ConflictEvaluator:
    @staticmethod
    def payload_sha256(payload: Mapping[str, object]) -> str:
        encoded = json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        return sha256(encoded).hexdigest()

    def evaluate_existing_crosswalk(
        self,
        *,
        source_record_id: str,
        proposed_canonical_id: str,
        proposed_payload: Mapping[str, object],
        existing: ExistingCrosswalk | None,
    ) -> ConflictDecision:
        if existing is None:
            return ConflictDecision(())

        findings: list[ConflictFinding] = []
        digest = self.payload_sha256(proposed_payload)
        if existing.source_record_id != source_record_id:
            findings.append(
                ConflictFinding.create(
                    ConflictCode.CROSSWALK_CONFLICT,
                    source_record_id,
                    "existing crosswalk belongs to a different source record",
                )
            )
            return ConflictDecision(tuple(findings))

        if existing.canonical_id != proposed_canonical_id:
            findings.append(
                ConflictFinding.create(
                    ConflictCode.CROSSWALK_CONFLICT,
                    source_record_id,
                    "source record is already crosswalked to a different canonical identity",
                )
            )
            return ConflictDecision(tuple(findings))

        if existing.source_payload_sha256 == digest:
            findings.append(
                ConflictFinding.create(
                    ConflictCode.IDEMPOTENT_REUSE,
                    source_record_id,
                    "source payload and canonical target already match",
                )
            )
        else:
            findings.append(
                ConflictFinding.create(
                    ConflictCode.SOURCE_ID_CONFLICT,
                    source_record_id,
                    "source identity already exists with a different payload digest",
                )
            )
        return ConflictDecision(tuple(findings))

    @staticmethod
    def validate_coordinate(*, subject_id: str, longitude: float, latitude: float) -> ConflictDecision:
        findings: list[ConflictFinding] = []
        if not -180.0 <= float(longitude) <= 180.0 or not -90.0 <= float(latitude) <= 90.0:
            findings.append(
                ConflictFinding.create(
                    ConflictCode.COORDINATE_INVALID,
                    subject_id,
                    "longitude must be [-180,180] and latitude must be [-90,90]",
                )
            )
        return ConflictDecision(tuple(findings))


__all__ = [
    "ConflictCode",
    "ConflictDisposition",
    "ConflictFinding",
    "ExistingCrosswalk",
    "ConflictDecision",
    "ConflictEvaluator",
]
