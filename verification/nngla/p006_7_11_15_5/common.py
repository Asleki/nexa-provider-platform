"""Shared, credential-safe Phase-F helpers for P006.7.11.15.5."""
from __future__ import annotations

import getpass
from datetime import date
import json
import os
from pathlib import Path
import subprocess
from typing import Iterable

from registries.nngla.spatial_realization.contracts import RepairMode
from registries.nngla.spatial_realization.selection import eligible_city_root_ids


def repository_revision() -> str:
    configured = str(os.environ.get("NPP_REPOSITORY_REVISION", "")).strip()
    if configured:
        return configured
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError("repository revision is unavailable; set NPP_REPOSITORY_REVISION")
    return proc.stdout.strip()


def selected_roots(*, roots: Iterable[str] | None, all_cities: bool) -> tuple[str, ...]:
    if all_cities and roots:
        raise ValueError("use either --all-cities or --roots, not both")
    if all_cities:
        return eligible_city_root_ids()
    values = tuple(roots or ())
    if not values:
        raise ValueError("--roots or --all-cities is required")
    return values


def connect_postgresql():
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover - operator environment gate
        raise RuntimeError("psycopg is required for Phase-F PostgreSQL verification") from exc

    required = ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER")
    missing = [name for name in required if not str(os.environ.get(name, "")).strip()]
    if missing:
        raise RuntimeError("missing PostgreSQL environment variables: " + ",".join(missing))

    password = getpass.getpass("PostgreSQL password: ")
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=password,
        sslmode=os.environ.get("PGSSLMODE", "require"),
        connect_timeout=int(os.environ.get("PGCONNECT_TIMEOUT", "30")),
    )



def effective_date(value: str | None = None) -> str:
    text = str(value or date.today().isoformat()).strip()
    try:
        return date.fromisoformat(text).isoformat()
    except ValueError as exc:
        raise ValueError("effective date must be ISO YYYY-MM-DD") from exc

def repair_mode(value: str) -> RepairMode:
    normalized = str(value).strip().upper().replace("-", "_")
    return RepairMode(normalized)


def preview_payload(preview) -> dict[str, object]:
    actions_by_root: dict[str, list[dict[str, object]]] = {}
    for item in preview.reconciliation:
        actions_by_root.setdefault(item.root_place_id, []).append({
            "subjectId": item.subject_id,
            "subjectType": item.subject_type.value,
            "geometryRole": item.geometry_role.value,
            "action": item.action.value,
            "reason": item.reason,
            "existingGeometryId": item.existing_geometry_id or None,
            "sourceCandidateId": item.source_candidate_id,
            "candidateChecksum": item.candidate_checksum,
        })

    assessments = []
    for assessment in preview.assessments:
        closure = next(item for item in preview.closures if item.root.place_id == assessment.root_place_id)
        assessments.append({
            "rootPlaceId": assessment.root_place_id,
            "displayName": closure.root.canonical_name,
            "administrativeRootId": closure.root.administrative_area_id,
            "validationParentId": closure.root.validation_parent_id,
            "supportingSpatialPointId": closure.supporting_spatial_point_id,
            "exhaustiveChildIds": [item.subject_id for item in closure.exhaustive_children],
            "overlayIds": [item.subject_id for item in closure.overlays],
            "regionalPartitionPeerIds": [item.subject_id for item in closure.regional_partition_peers],
            "repairApplied": assessment.repair_applied,
            "executionReady": assessment.execution_ready,
            "findings": [{
                "findingId": finding.finding_id,
                "ruleCode": finding.rule_code,
                "severity": finding.severity.value,
                "status": finding.status.value,
                "subjectId": finding.subject_id,
                "relatedSubjectId": finding.related_subject_id or None,
                "predicate": finding.predicate or None,
                "actual": finding.actual or None,
                "assessmentStage": finding.assessment_stage.value,
                "rawPredicateResult": finding.raw_predicate_result or None,
                "differenceDimension": finding.difference_dimension,
                "measurementMethod": finding.measurement_method or None,
                "areaKm2": finding.area_km2,
                "areaRatio": finding.area_ratio,
                "residualClass": finding.residual_class,
                "differenceBbox": finding.difference_bbox or None,
                "representativePoint": finding.representative_point or None,
                "repairEligibility": finding.repair_eligibility,
                "repairStrategy": finding.repair_strategy or None,
            } for finding in assessment.findings],
            "actions": actions_by_root.get(assessment.root_place_id, []),
        })

    return {
        "planId": preview.plan_id,
        "planVersion": preview.plan_version,
        "databaseName": preview.database_name,
        "environmentName": preview.environment_name,
        "repositoryRevision": preview.repository_revision,
        "sourceSha256": preview.source_sha256,
        "targetSnapshotDigest": preview.target_snapshot_digest,
        "topologyPolicyId": preview.topology_policy_id,
        "repairPolicyId": preview.repair_policy_id,
        "repairMode": preview.repair_mode,
        "effectiveDate": preview.effective_date,
        "normalizedRootIds": list(preview.normalized_root_ids),
        "executionReady": preview.execution_ready,
        "candidateGeometryWrites": preview.candidate_geometry_writes,
        "candidateAssociations": preview.candidate_associations,
        "plannedGeometryWrites": preview.planned_geometry_writes,
        "plannedAssociations": preview.planned_associations,
        "fingerprint": preview.fingerprint,
        "confirmationToken": f"REALIZE-NNGLA-CITIES::{preview.database_name}::{preview.fingerprint}",
        "assessments": assessments,
    }


def write_json(payload: dict[str, object], output: str | None) -> None:
    encoded = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    print(encoded)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded + "\n", encoding="utf-8")
