"""Bundle 17A immutable spatial-source inventory and contract validation."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
import csv
import re

from .contracts import (
    AllowedMigrationAction,
    SpatialEvidenceRole,
    SpatialSourceClassification,
    SpatialSourceManifestEntry,
)

ROOT = Path(__file__).resolve().parents[3]
SOURCE_ROOT = ROOT / "data" / "novegeo" / "nngla" / "spatial-fabric" / "source"
BASE_NAMESPACE_PATH = ROOT / "data" / "novegeo" / "nngla" / "foundation" / "source" / "novegeo_code_namespace.csv"
BASE_FORMAT_PATH = ROOT / "data" / "novegeo" / "nngla" / "foundation" / "source" / "novegeo_identifier_format_register.csv"
MANIFEST_PATH = SOURCE_ROOT / "00_manifest" / "novegeo_spatial_source_manifest_v002.csv"
NAMESPACE_EXTENSION_PATH = SOURCE_ROOT / "03_authority_identifiers" / "novegeo_code_namespace_extensions_v001.csv"
FORMAT_EXTENSION_PATH = SOURCE_ROOT / "03_authority_identifiers" / "novegeo_identifier_format_extensions_v001.csv"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _bool(value: str) -> bool:
    text = str(value).strip().lower()
    if text not in {"true", "false"}:
        raise ValueError(f"invalid boolean {value!r}")
    return text == "true"


def load_manifest(path: Path = MANIFEST_PATH) -> tuple[SpatialSourceManifestEntry, ...]:
    entries = tuple(
        SpatialSourceManifestEntry(
            source_file_id=row["source_file_id"],
            filename=row["filename"],
            source_path=row["source_path"],
            source_family=row["source_family"],
            dataset_id=row["dataset_id"],
            dataset_version=row["dataset_version"],
            source_sha256=row["source_sha256"],
            record_count=int(row["record_count"]),
            classification=SpatialSourceClassification(row["classification"]),
            evidence_role=SpatialEvidenceRole(row["evidence_role"]),
            contains_coordinates=_bool(row["contains_coordinates"]),
            contains_geometry=_bool(row["contains_geometry"]),
            contains_names=_bool(row["contains_names"]),
            already_canonical_domain=row["already_canonical_domain"],
            allowed_migration_action=AllowedMigrationAction(row["allowed_migration_action"]),
            status=row["status"],
        )
        for row in _rows(path)
    )
    ids = [entry.source_file_id for entry in entries]
    paths = [entry.source_path for entry in entries]
    if len(ids) != len(set(ids)) or len(paths) != len(set(paths)):
        raise ValueError("spatial source manifest contains duplicate identities or paths")
    return entries


def source_path(entry: SpatialSourceManifestEntry) -> Path:
    return ROOT / entry.source_path


def source_row_count(path: Path) -> int:
    return len(_rows(path))


def source_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def load_identifier_formats() -> tuple[dict[str, str], ...]:
    """Return combined immutable base + additive Bundle 17A format contracts."""
    return tuple(_rows(BASE_FORMAT_PATH) + _rows(FORMAT_EXTENSION_PATH))


def validate_identifier_extension_contracts() -> tuple[str, ...]:
    """Return findings for additive namespace/format contracts without editing base files."""
    base_namespaces = _rows(BASE_NAMESPACE_PATH)
    extension_namespaces = _rows(NAMESPACE_EXTENSION_PATH)
    base_formats = _rows(BASE_FORMAT_PATH)
    extension_formats = _rows(FORMAT_EXTENSION_PATH)
    findings: list[str] = []
    base_ns_ids = {row["namespace_id"] for row in base_namespaces}
    ext_ns_ids = {row["namespace_id"] for row in extension_namespaces}
    if base_ns_ids & ext_ns_ids:
        findings.append("NAMESPACE_ID_REDEFINITION")
    base_fmt_ids = {row["identifier_format_id"] for row in base_formats}
    ext_fmt_ids = {row["identifier_format_id"] for row in extension_formats}
    if base_fmt_ids & ext_fmt_ids:
        findings.append("IDENTIFIER_FORMAT_REDEFINITION")
    known_ns = base_ns_ids | ext_ns_ids
    for row in extension_formats:
        if row["namespace_id"] not in known_ns:
            findings.append(f"UNKNOWN_NAMESPACE:{row['identifier_format_id']}")
            continue
        try:
            pattern = re.compile(row["regex_pattern"])
        except re.error:
            findings.append(f"INVALID_REGEX:{row['identifier_format_id']}")
            continue
        if pattern.fullmatch(row["example_identifier"]) is None:
            findings.append(f"EXAMPLE_MISMATCH:{row['identifier_format_id']}")
        if row["issuing_authority_code"] != "NNGLA" or row["immutable"].lower() != "true":
            findings.append(f"AUTHORITY_OR_IMMUTABILITY:{row['identifier_format_id']}")
    return tuple(findings)


@lru_cache(maxsize=1)
def _compiled_formats() -> tuple[tuple[str, re.Pattern[str]], ...]:
    out: list[tuple[str, re.Pattern[str]]] = []
    for row in load_identifier_formats():
        out.append((row["identifier_format_id"], re.compile(row["regex_pattern"])))
    return tuple(out)


def validate_governed_identifier(value: str) -> bool:
    """Validate only NNGLA/NoveGeo governed identifier-looking values.

    Source identities such as ``river:novegeo:*`` are deliberately outside this
    check.  CRS and dataset codes are not object identifiers and are likewise
    excluded.
    """
    text = str(value).strip()
    if not text.startswith(("NG-", "NGP-", "NGR-", "NV-")):
        return True
    return any(pattern.fullmatch(text) for _, pattern in _compiled_formats())


@dataclass(frozen=True, slots=True)
class SourceContractResult:
    source_file_id: str
    source_path: str
    expected_sha256: str
    actual_sha256: str
    expected_row_count: int
    actual_row_count: int
    header_present: bool
    namespace_contract_status: str
    contract_status: str
    findings: str


def validate_source_contract(entry: SpatialSourceManifestEntry) -> SourceContractResult:
    path = source_path(entry)
    findings: list[str] = []
    if not path.is_file():
        return SourceContractResult(
            entry.source_file_id, entry.source_path, entry.source_sha256, "", entry.record_count, 0,
            False, "NOT_CHECKED", "FAIL", "SOURCE_FILE_MISSING",
        )
    actual_sha = source_sha256(path)
    rows = _rows(path)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        header = next(csv.reader(handle), [])
    if actual_sha != entry.source_sha256:
        findings.append("SHA256_MISMATCH")
    if len(rows) != entry.record_count:
        findings.append("ROW_COUNT_MISMATCH")
    if not header:
        findings.append("HEADER_MISSING")

    bad_ids: set[str] = set()
    for row in rows:
        for field, raw in row.items():
            if not field.endswith("_id") or not raw:
                continue
            for token in str(raw).split("|"):
                token = token.strip()
                if token and not validate_governed_identifier(token):
                    bad_ids.add(token)
    if bad_ids:
        findings.append("UNREGISTERED_GOVERNED_IDENTIFIER:" + "|".join(sorted(bad_ids)[:12]))
    status = "PASS" if not findings else "FAIL"
    return SourceContractResult(
        entry.source_file_id,
        entry.source_path,
        entry.source_sha256,
        actual_sha,
        entry.record_count,
        len(rows),
        bool(header),
        "PASS" if not bad_ids else "FAIL",
        status,
        ";".join(findings),
    )


def validate_all_sources(entries: tuple[SpatialSourceManifestEntry, ...] | None = None) -> tuple[SourceContractResult, ...]:
    current = entries or load_manifest()
    return tuple(validate_source_contract(entry) for entry in current)


__all__ = [
    "ROOT", "SOURCE_ROOT", "MANIFEST_PATH", "NAMESPACE_EXTENSION_PATH", "FORMAT_EXTENSION_PATH",
    "load_manifest", "source_path", "source_row_count", "source_sha256",
    "load_identifier_formats", "validate_identifier_extension_contracts", "validate_governed_identifier",
    "SourceContractResult", "validate_source_contract", "validate_all_sources",
]
