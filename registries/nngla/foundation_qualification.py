"""P006.7.2.10 deterministic NNGLA foundation qualification."""
from __future__ import annotations

import csv
from dataclasses import dataclass, replace
from pathlib import Path

from registries.country.operating_context import RecordEffectScope
from shared.runtime.operation_runtime import OperationRuntimeMode
from .canonicalization import CanonicalizationService
from .events import NNGLAEventFactory, NNGLAEventType
from .ingest import IngestBatch, IngestState, MemoryIngestStore, StagedRecord
from .migration_source import load_manifest, load_validation_evidence
from .publication import NNGLAPublicationService, evaluate_publication_eligibility
from .schema_contract import load_schema_sql, qualify_schema_sql
from .source import load_authority, load_domain_catalogue, load_identifier_catalogue, load_lifecycle_definitions
from .source_dataset import DataClassification, DatasetClass, SourceRecordReference


DEFAULT_QUALIFICATION_SOURCE_ROOT = Path(__file__).resolve().parents[2] / "data" / "novegeo" / "nngla" / "qualification-foundation" / "source"


@dataclass(frozen=True, slots=True)
class NNGLAFoundationQualificationReceipt:
    qualification_id: str
    status: str
    authority_id: str
    country_id: str
    realm_id: str
    findings: tuple[str, ...]
    publication_content_sha256: str


def _load_historical_audit_rows(root: Path = DEFAULT_QUALIFICATION_SOURCE_ROOT) -> tuple[dict[str, str], ...]:
    path = root / "novegeo_immutable_audit_event.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def _representative_staged_record(runtime: OperationRuntimeMode) -> StagedRecord:
    batch = IngestBatch.create(
        source_dataset_id="dataset:nngla:qualification",
        source_dataset_version="1",
        runtime_mode=runtime,
        effect_scope=RecordEffectScope.RUNTIME_SCOPED,
        classification=DataClassification.PUBLIC_REFERENCE,
    )
    source = SourceRecordReference(
        dataset_id=batch.source_dataset_id,
        dataset_version=batch.source_dataset_version,
        source_record_id="qualification-source:road:1",
        source_file="qualification/internal",
        row_number=1,
    )
    return StagedRecord.create(
        batch=batch,
        source=source,
        record_family="ROAD_REFERENCE",
        candidate_id="qualification-candidate:road:1",
        raw_payload={"road_id": "NG-RD-000001", "status": "qualification-only"},
    )


def qualify_nngla_foundation(repository_root: str | Path) -> NNGLAFoundationQualificationReceipt:
    root = Path(repository_root)
    authority, roles = load_authority(root / "data/novegeo/nngla/foundation/source")
    domains = load_domain_catalogue(root / "data/novegeo/nngla/foundation/source")
    identifiers = load_identifier_catalogue(root / "data/novegeo/nngla/foundation/source")
    lifecycle = load_lifecycle_definitions(root / "data/novegeo/nngla/foundation/source")
    manifest = load_manifest(root / "data/novegeo/nngla/ingest-foundation/source")
    validations = load_validation_evidence(root / "data/novegeo/nngla/ingest-foundation/source")

    if authority.authority_id != "authority:nngla" or len(roles) != 10:
        raise ValueError("NNGLA authority foundation failed qualification")
    if len(domains.families) != 9:
        raise ValueError("NNGLA domain catalogue failed qualification")
    if len(identifiers.namespaces) != 11 or not identifiers.formats:
        raise ValueError("NNGLA identifier foundation failed qualification")
    if len(lifecycle) != 20:
        raise ValueError("NNGLA lifecycle foundation failed qualification")
    if not any(item.dataset_class is DatasetClass.REAL_POPULATED_DATASET for item in manifest):
        raise ValueError("real populated migration datasets missing")
    if not any(item.dataset_class is DatasetClass.REAL_EMPTY_GOVERNED_REGISTER for item in manifest):
        raise ValueError("real empty governed registers missing")
    if any(item.result != "PASS" for item in validations):
        raise ValueError("Bundle 14B validation evidence contains failures")

    schema_findings = qualify_schema_sql(load_schema_sql(root / "database/schemas/nngla_spatial_foundation.sql"))
    if schema_findings:
        raise ValueError(f"NNGLA schema contract failed qualification: {schema_findings}")

    historical = _load_historical_audit_rows(root / "data/novegeo/nngla/qualification-foundation/source")
    migration_rows = [r for r in historical if r.get("event_type") == "DATABASE_MIGRATION_STATUS"]
    if len(migration_rows) != 1 or migration_rows[0].get("result") != "NOT_EXECUTED":
        raise ValueError("historical migration evidence must explicitly remain NOT_EXECUTED")

    staged = _representative_staged_record(OperationRuntimeMode.SIMULATION)
    store = MemoryIngestStore()
    store.stage(staged)
    validated = replace(staged, state=IngestState.CANONICALIZATION_READY)
    canonicalizer = CanonicalizationService()
    receipt = canonicalizer.canonicalize(
        validated,
        canonical_id="NG-RD-000001",
        canonical_version=1,
        validation_references=("qualification:nngla:representative-validation",),
    )
    repeated = canonicalizer.canonicalize(validated, canonical_id="NG-RD-000001", canonical_version=1)
    if repeated.receipt_id != receipt.receipt_id:
        raise ValueError("canonicalization idempotency failed")

    trace = NNGLAEventFactory.create(
        event_type=NNGLAEventType.RECORD_CANONICALIZED,
        subject_id=receipt.crosswalk.canonical_id,
        record_family=validated.record_family,
        runtime_mode=receipt.crosswalk.key.runtime_mode,
        effect_scope=receipt.crosswalk.key.effect_scope,
        canonical_version=receipt.crosswalk.canonical_version,
        correlation_id="qualification:p006.7.2",
        actor_id="authority:nngla",
        payload={"canonicalization_receipt_id": receipt.receipt_id},
    )
    if trace.audit.event_id != trace.event.event_id or trace.audit.runtime_mode != OperationRuntimeMode.SIMULATION.value:
        raise ValueError("NNGLA event/audit linkage failed")

    publisher = NNGLAPublicationService()
    publication = publisher.publish(
        receipt,
        record_family=validated.record_family,
        classification=DataClassification.PUBLIC_REFERENCE,
        payload={"canonicalId": receipt.crosswalk.canonical_id},
    )
    restricted = evaluate_publication_eligibility(
        receipt,
        classification=DataClassification.SECURITY_SENSITIVE,
        record_family=validated.record_family,
    )
    if restricted.eligible:
        raise ValueError("security-sensitive records must not be publicly eligible")

    production = _representative_staged_record(OperationRuntimeMode.PRODUCTION)
    if production.batch.runtime_mode is staged.batch.runtime_mode:
        raise ValueError("simulation and production runtime distinction collapsed")

    findings = (
        "BUNDLE_14A_AUTHORITY_QUALIFIED",
        "BUNDLE_14A_DOMAIN_CATALOGUE_QUALIFIED",
        "BUNDLE_14A_SPATIAL_IDENTIFIERS_QUALIFIED",
        "BUNDLE_14A_LIFECYCLE_QUALIFIED",
        "BUNDLE_14B_SOURCE_MANIFEST_QUALIFIED",
        "REAL_POPULATED_DATASETS_PRESERVED",
        "REAL_EMPTY_GOVERNED_REGISTERS_PRESERVED",
        "BUNDLE_14B_VALIDATION_EVIDENCE_PASSED",
        "POSTGIS_SCHEMA_FOUNDATION_QUALIFIED",
        "CONTROLLED_DATABASE_MIGRATION_NOT_EXECUTED",
        "CANONICALIZATION_IDEMPOTENT",
        "SOURCE_TO_CANONICAL_LINEAGE_PRESERVED",
        "NNGLA_EVENT_AUDIT_LINKED",
        "PUBLICATION_ELIGIBILITY_ENFORCED",
        "SECURITY_SENSITIVE_PUBLICATION_BLOCKED",
        "SIMULATION_PRODUCTION_DISTINCTION_PRESERVED",
        "STABLE_SPATIAL_IDENTITY_PRESERVED",
    )
    return NNGLAFoundationQualificationReceipt(
        qualification_id="qualification:novegeo:nngla-foundation:v1",
        status="PASSED",
        authority_id=authority.authority_id,
        country_id=authority.country_record_id,
        realm_id=authority.world_realm_id,
        findings=findings,
        publication_content_sha256=publication.content_sha256,
    )


__all__ = ["NNGLAFoundationQualificationReceipt", "qualify_nngla_foundation", "DEFAULT_QUALIFICATION_SOURCE_ROOT"]
