"""P006.7.2.5 NNGLA source-dataset and provenance contracts.

Source datasets are immutable migration evidence.  They are never canonical
runtime storage.  The contracts deliberately retain file/hash/row lineage so a
later canonical NNGLA record can always be traced back to its source evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import Enum
from hashlib import sha256
from pathlib import Path
import re

_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class DatasetClass(str, Enum):
    REAL_POPULATED_DATASET = "REAL_POPULATED_DATASET"
    REAL_COMPLETE_CONTROLLED_VOCABULARY = "REAL_COMPLETE_CONTROLLED_VOCABULARY"
    REAL_EMPTY_GOVERNED_REGISTER = "REAL_EMPTY_GOVERNED_REGISTER"


class MigrationEligibility(str, Enum):
    READY_FOR_MIGRATION_PLANNING = "READY_FOR_MIGRATION_PLANNING"
    DEFERRED_SPATIAL_OR_LEGAL = "DEFERRED_SPATIAL_OR_LEGAL"


class DataClassification(str, Enum):
    PUBLIC = "PUBLIC"
    PUBLIC_REFERENCE = "PUBLIC_REFERENCE"
    INTERNAL = "INTERNAL"
    RESTRICTED = "RESTRICTED"
    LEGAL_RECORD = "LEGAL_RECORD"
    SECURITY_SENSITIVE = "SECURITY_SENSITIVE"


@dataclass(frozen=True, slots=True)
class SourceDatasetManifestEntry:
    catalogue_id: str
    folder_family: str
    file_name: str
    row_count: int | None
    dataset_class: DatasetClass
    migration_eligibility: MigrationEligibility
    source_basis: str
    spatial_dependency: bool
    status: str

    def __post_init__(self) -> None:
        if not self.catalogue_id.startswith("CAT-"):
            raise ValueError("catalogue_id must use CAT- namespace")
        if self.row_count < 0:
            raise ValueError("row_count cannot be negative")
        if not self.folder_family or not self.file_name:
            raise ValueError("folder_family and file_name are required")

    @property
    def relative_path(self) -> str:
        return f"{self.folder_family}/{self.file_name}"


@dataclass(frozen=True, slots=True)
class SourceArtifactEvidence:
    hash_record_id: str
    file_path: str
    sha256_hex: str
    byte_size: int
    calculated_at: date

    def __post_init__(self) -> None:
        if not self.hash_record_id.startswith("HASH-"):
            raise ValueError("hash_record_id must use HASH- namespace")
        if not _SHA256.fullmatch(self.sha256_hex):
            raise ValueError("sha256_hex must contain 64 lowercase hex characters")
        if self.byte_size < 0:
            raise ValueError("byte_size cannot be negative")
        if not self.file_path:
            raise ValueError("file_path is required")

    def verify(self, path: Path) -> bool:
        data = Path(path).read_bytes()
        return len(data) == self.byte_size and sha256(data).hexdigest() == self.sha256_hex


@dataclass(frozen=True, slots=True)
class ValidationEvidence:
    validation_id: str
    file_path: str
    validation_type: str
    row_count: int
    result: str
    error_count: int
    details: str
    validated_at: date

    def __post_init__(self) -> None:
        if not self.validation_id.startswith("VAL-"):
            raise ValueError("validation_id must use VAL- namespace")
        if self.row_count is not None and self.row_count < 0:
            raise ValueError("row_count cannot be negative")
        if self.error_count < 0:
            raise ValueError("error_count cannot be negative")
        if self.result not in {"PASS", "FAIL"}:
            raise ValueError("result must be PASS or FAIL")
        if self.result == "PASS" and self.error_count:
            raise ValueError("PASS validation cannot report errors")


@dataclass(frozen=True, slots=True)
class SourceRecordReference:
    dataset_id: str
    dataset_version: str
    source_record_id: str
    source_file: str
    row_number: int | None = None

    def __post_init__(self) -> None:
        if not self.dataset_id.startswith("dataset:"):
            raise ValueError("dataset_id must use dataset: namespace")
        if not self.dataset_version:
            raise ValueError("dataset_version is required")
        if not self.source_record_id:
            raise ValueError("source_record_id is required")
        if not self.source_file:
            raise ValueError("source_file is required")
        if self.row_number is not None and self.row_number < 1:
            raise ValueError("row_number must be positive when supplied")


__all__ = [
    "DatasetClass", "MigrationEligibility", "DataClassification",
    "SourceDatasetManifestEntry", "SourceArtifactEvidence", "ValidationEvidence",
    "SourceRecordReference",
]
