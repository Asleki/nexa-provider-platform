"""P006.UI.10.2.B — Stable contracts for governed Enigma catalogue admission."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


PERIODS = ("Morning", "Noon", "Evening")
WORD_LENGTHS = (3, 4, 5)
EXPECTED_ROW_COUNT = 31 * len(PERIODS)
EXPECTED_TOTAL_ROW_COUNT = EXPECTED_ROW_COUNT * len(WORD_LENGTHS)
EXPECTED_KEYS = frozenset(
    (day, period)
    for day in range(1, 32)
    for period in PERIODS
)


class EnigmaCatalogueAdmissionError(RuntimeError):
    """Base error for governed Enigma catalogue qualification/admission."""


class EnigmaSourceQualificationError(EnigmaCatalogueAdmissionError, ValueError):
    """Raised when a private source is not exactly qualified."""


class EnigmaDatabaseQualificationError(EnigmaCatalogueAdmissionError):
    """Raised when the PostgreSQL authority is unsafe for admission/read-back."""


@dataclass(frozen=True, slots=True)
class EnigmaSourceSpec:
    word_length: int
    relative_path: Path
    source_reference: str
    expected_sha256: str
    catalogue_id: str
    catalogue_version: int = 1

    def __post_init__(self) -> None:
        if self.word_length not in WORD_LENGTHS:
            raise ValueError("word_length must be 3, 4 or 5")
        if not self.source_reference or self.source_reference != self.relative_path.as_posix():
            raise ValueError("source_reference must equal the repository-relative source path")
        if len(self.expected_sha256) != 64 or any(ch not in "0123456789abcdef" for ch in self.expected_sha256):
            raise ValueError("expected_sha256 must be 64 lowercase hexadecimal characters")
        if not self.catalogue_id.strip() or self.catalogue_id != self.catalogue_id.strip():
            raise ValueError("catalogue_id must be a non-blank canonical token")
        if self.catalogue_version <= 0:
            raise ValueError("catalogue_version must be positive")

    def resolve(self, repository_root: Path) -> Path:
        return Path(repository_root) / self.relative_path


@dataclass(frozen=True, slots=True)
class QualifiedEnigmaRow:
    day_of_month: int
    period: str
    words: tuple[str, str, str]

    @property
    def key(self) -> tuple[int, str]:
        return self.day_of_month, self.period


@dataclass(frozen=True, slots=True)
class EnigmaRepetitionMetrics:
    distinct_challenge_triples: int
    repeated_challenge_triple_groups: int
    repeated_challenge_triple_occurrences: int
    distinct_lookup_tokens: int
    repeated_lookup_token_groups: int
    repeated_lookup_token_occurrences: int
    distinct_expected_signatures: int
    expected_signature_collision_groups: int
    expected_signature_collision_occurrences: int


@dataclass(frozen=True, slots=True)
class QualifiedEnigmaSource:
    spec: EnigmaSourceSpec
    byte_size: int
    sha256: str
    encoding: str
    newline_style: str
    trailing_newline: bool
    row_count: int
    rows: tuple[QualifiedEnigmaRow, ...]
    metrics: EnigmaRepetitionMetrics

    def shared_row_map(self) -> Mapping[tuple[int, str], QualifiedEnigmaRow]:
        return {row.key: row for row in self.rows}

    def safe_summary(self) -> dict[str, object]:
        return {
            "wordLength": self.spec.word_length,
            "sourceReference": self.spec.source_reference,
            "sourceSha256": self.sha256,
            "byteSize": self.byte_size,
            "encoding": self.encoding,
            "newlineStyle": self.newline_style,
            "trailingNewline": self.trailing_newline,
            "rowCount": self.row_count,
            "catalogueId": self.spec.catalogue_id,
            "catalogueVersion": self.spec.catalogue_version,
            "distinctChallengeTriples": self.metrics.distinct_challenge_triples,
            "repeatedChallengeTripleGroups": self.metrics.repeated_challenge_triple_groups,
            "repeatedChallengeTripleOccurrences": self.metrics.repeated_challenge_triple_occurrences,
            "distinctLookupTokens": self.metrics.distinct_lookup_tokens,
            "repeatedLookupTokenGroups": self.metrics.repeated_lookup_token_groups,
            "repeatedLookupTokenOccurrences": self.metrics.repeated_lookup_token_occurrences,
            "distinctExpectedSignatures": self.metrics.distinct_expected_signatures,
            "expectedSignatureCollisionGroups": self.metrics.expected_signature_collision_groups,
            "expectedSignatureCollisionOccurrences": self.metrics.expected_signature_collision_occurrences,
        }


@dataclass(frozen=True, slots=True)
class PostgreSQLPreflightReport:
    database_name: str
    tls_active: bool
    repository_migration_count: int
    database_migration_count: int
    migration_tail_sequence: int
    migration_tail_id: str
    nexilabs_auth_tables: tuple[str, ...]
    public_schema_privilege_count: int
    public_table_privilege_count: int
    principal_count: int
    catalogue_count: int
    catalogue_entry_count: int
    profile_count: int
    principal_profile_assignment_count: int

    def safe_summary(self) -> dict[str, object]:
        return {
            "databaseName": self.database_name,
            "tlsActive": self.tls_active,
            "repositoryMigrationCount": self.repository_migration_count,
            "databaseMigrationCount": self.database_migration_count,
            "migrationTailSequence": self.migration_tail_sequence,
            "migrationTailId": self.migration_tail_id,
            "nexilabsAuthTables": list(self.nexilabs_auth_tables),
            "publicSchemaPrivilegeCount": self.public_schema_privilege_count,
            "publicTablePrivilegeCount": self.public_table_privilege_count,
            "principalCount": self.principal_count,
            "catalogueCount": self.catalogue_count,
            "catalogueEntryCount": self.catalogue_entry_count,
            "profileCount": self.profile_count,
            "principalProfileAssignmentCount": self.principal_profile_assignment_count,
        }


@dataclass(frozen=True, slots=True)
class EnigmaAdmissionReceipt:
    catalogue_count: int
    entry_count: int
    active_catalogue_count: int
    catalogue_ids: tuple[str, ...]

    def safe_summary(self) -> dict[str, object]:
        return {
            "catalogueCount": self.catalogue_count,
            "entryCount": self.entry_count,
            "activeCatalogueCount": self.active_catalogue_count,
            "catalogueIds": list(self.catalogue_ids),
        }


@dataclass(frozen=True, slots=True)
class EnigmaReadBackReceipt:
    catalogue_count: int
    entry_count: int
    exact_parity: bool

    def safe_summary(self) -> dict[str, object]:
        return {
            "catalogueCount": self.catalogue_count,
            "entryCount": self.entry_count,
            "exactParity": self.exact_parity,
        }


@dataclass(frozen=True, slots=True)
class EnigmaAdapterQualificationReceipt:
    profile_id: str
    qualified_word_lengths: tuple[int, ...]
    cleanup_proven: bool

    def safe_summary(self) -> dict[str, object]:
        return {
            "profileId": self.profile_id,
            "qualifiedWordLengths": list(self.qualified_word_lengths),
            "cleanupProven": self.cleanup_proven,
        }
