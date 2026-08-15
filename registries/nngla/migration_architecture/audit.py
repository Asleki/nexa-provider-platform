"""P006.7.11.1 read-only Name Catalogue/NNGLA architecture audit."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from registries.nngla.schema_contract import NNGLA_SCHEMA_SQL, load_schema_sql
from registries.nngla.schema15a_contract import SCHEMA15A_SQL, load_schema15a_sql
from registries.nngla.schema15b_contract import SCHEMA15B_SQL, load_schema15b_sql
from registries.nngla.schema15c_contract import SCHEMA15C_SQL, load_schema15c_sql


ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS = ROOT / "database" / "migrations"

NAME_MIGRATION_FILES = (
    "m009_10_04_name_catalogue.sql",
    "m009_12_06_name_authority.sql",
    "m009_12_09_name_authority_generation.sql",
    "m009_12_12_name_authority_application.sql",
    "m009_13_10_reference_registry_authoring.sql",
)


@dataclass(frozen=True, slots=True)
class AuditFinding:
    code: str
    severity: str
    subject: str
    detail: str


@dataclass(frozen=True, slots=True)
class ArchitectureAuditReport:
    name_migration_files: tuple[str, ...]
    nngla_schema_files: tuple[str, ...]
    findings: tuple[AuditFinding, ...]

    @property
    def blocking_findings(self) -> tuple[AuditFinding, ...]:
        return tuple(f for f in self.findings if f.severity == "BLOCKING")


class ArchitectureAuditor:
    """Static/read-only audit; never connects to or writes PostgreSQL."""

    def audit(self) -> ArchitectureAuditReport:
        findings: list[AuditFinding] = []
        self._audit_name_migrations(findings)
        self._audit_nngla_schemas(findings)
        return ArchitectureAuditReport(
            NAME_MIGRATION_FILES,
            tuple(str(p.relative_to(ROOT)) for p in (NNGLA_SCHEMA_SQL, SCHEMA15A_SQL, SCHEMA15B_SQL, SCHEMA15C_SQL)),
            tuple(findings),
        )

    @staticmethod
    def _contains(sql: str, pattern: str) -> bool:
        return re.search(pattern, sql, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL) is not None

    def _audit_name_migrations(self, findings: list[AuditFinding]) -> None:
        missing = [name for name in NAME_MIGRATION_FILES if not (MIGRATIONS / name).exists()]
        for name in missing:
            findings.append(AuditFinding("NAME_MIGRATION_MISSING", "BLOCKING", name, "required migration file missing"))
        if missing:
            return

        name_catalogue = (MIGRATIONS / NAME_MIGRATION_FILES[0]).read_text(encoding="utf-8")
        if not self._contains(name_catalogue, r"unique\s*\(\s*runtime_mode\s*,\s*name_kind\s*,\s*search_value\s*\)"):
            findings.append(AuditFinding(
                "NAME_SEMANTIC_UNIQUENESS_MISSING", "BLOCKING", NAME_MIGRATION_FILES[0],
                "canonical name migration must preserve runtime/kind/search-value semantic uniqueness",
            ))

        generation = (MIGRATIONS / NAME_MIGRATION_FILES[2]).read_text(encoding="utf-8")
        if not self._contains(generation, r"batch_size.+between\s+1\s+and\s+10000"):
            findings.append(AuditFinding(
                "NAME_BATCH_LIMIT_NOT_DETECTED", "REVIEW", NAME_MIGRATION_FILES[2],
                "expected governed generation batch range 1..10000 was not detected",
            ))

        application = (MIGRATIONS / NAME_MIGRATION_FILES[3]).read_text(encoding="utf-8")
        for token in ("idempotency_key", "request_hash", "conflict_count", "checksum"):
            if token not in application:
                findings.append(AuditFinding(
                    "NAME_RECEIPT_CONTROL_MISSING", "BLOCKING", NAME_MIGRATION_FILES[3],
                    f"expected receipt/audit control missing: {token}",
                ))

    def _audit_nngla_schemas(self, findings: list[AuditFinding]) -> None:
        foundation = load_schema_sql()
        places = load_schema15a_sql()
        roads = load_schema15b_sql()
        cadastre = load_schema15c_sql()

        for token in (
            "nngla_staged_record",
            "nngla_quarantine_record",
            "nngla_canonical_crosswalk",
            "nngla_canonicalization_receipt",
        ):
            if token not in foundation:
                findings.append(AuditFinding("NNGLA_FOUNDATION_CONTROL_MISSING", "BLOCKING", str(NNGLA_SCHEMA_SQL), token))

        # Bundle 16A explicitly records this as a pre-migration architecture gap.
        # We do not rewrite the locked P006.7.4 contract here; later additive DDL
        # must introduce a canonical place identity before live population.
        if self._contains(places, r"create\s+table\s+geography\.nngla_place_reference\s*\(\s*source_place_code\s+text\s+primary\s+key"):
            findings.append(AuditFinding(
                "PLACE_CANONICAL_ID_REQUIRED",
                "BLOCKING",
                "geography.nngla_place_reference",
                "source_place_code is a source identity; additive migration architecture must introduce an immutable canonical place_id before population",
            ))

        if self._contains(places, r"create\s+table\s+geography\.nngla_administrative_area\s*\(\s*administrative_candidate_id\s+text\s+primary\s+key"):
            findings.append(AuditFinding(
                "ADMIN_CANONICAL_ID_REQUIRED",
                "BLOCKING",
                "geography.nngla_administrative_area",
                "administrative_candidate_id is candidate identity; additive migration architecture must introduce a canonical administrative_area_id before population",
            ))

        if "road_candidate_id" not in roads or "road_id" not in roads:
            findings.append(AuditFinding(
                "ROAD_CANDIDATE_CANONICAL_SEPARATION_MISSING", "BLOCKING", str(SCHEMA15B_SQL),
                "road schema must preserve candidate and canonical road identities",
            ))

        if "longitude double precision" not in roads.lower() or "latitude double precision" not in roads.lower():
            findings.append(AuditFinding(
                "COORDINATE_COLUMNS_NOT_DETECTED", "REVIEW", str(SCHEMA15B_SQL),
                "survey coordinate columns were not detected",
            ))
        if "between -180" not in roads.lower() or "between -90" not in roads.lower():
            findings.append(AuditFinding(
                "COORDINATE_RANGE_CHECK_NOT_DETECTED", "BLOCKING", str(SCHEMA15B_SQL),
                "longitude/latitude defensive range checks must remain present",
            ))

        if "parcel_id" not in cadastre or "title_id" not in cadastre:
            findings.append(AuditFinding(
                "LAND_IDENTITY_CONTRACT_MISSING", "BLOCKING", str(SCHEMA15C_SQL),
                "parcel/title identity contracts must remain available for later data plans",
            ))


__all__ = ["AuditFinding", "ArchitectureAuditReport", "ArchitectureAuditor", "NAME_MIGRATION_FILES"]
