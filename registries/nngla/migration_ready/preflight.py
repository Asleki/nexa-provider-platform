"""Fail-closed live target preflight for NNGLA Migration Ready."""
from __future__ import annotations

from pathlib import Path

from registries.nngla.spatial_fabric.bundle17e.qualification import bundle17e_is_qualified

from .baseline import verify_immutable_baseline
from .candidate_state import assess_candidate_state
from .contracts import TargetPreflight
from .empty_registers import assess_empty_registers, empty_registers_ready


REQUIRED_MIGRATION_IDS = (
    "m009_10_04_name_catalogue",
    "m009_12_06_name_authority",
    "m009_12_09_name_authority_generation",
    "m009_12_12_name_authority_application",
    "m009_13_10_reference_registry_authoring",
    "m004_01_02_world_geometry_authority",
    "m006_07_11_nngla_execution_foundation",
    "m006_07_11_nngla_identity_places_runtime",
    "m006_07_11_nngla_geometry_roads_runtime",
    "m006_07_11_nngla_cadastre_runtime",
    "m006_07_11_nngla_smart_addressing_sites",
    "m006_07_11_nngla_title_reservations_state_land_candidates",
    "m006_07_11_nngla_allocator_concurrency_recovery",
    "m006_07_11_nngla_geometry_change_lifecycle",
    "m006_07_11_nngla_feature_recognition_lifecycle",
    "m006_07_11_nngla_geographic_naming_gazette",
    "m006_07_11_nngla_runtime_command_services",
    "m006_07_11_nngla_spatial_query_read_models",
)

REQUIRED_RELATIONS = (
    "geography.nngla_source_dataset",
    "geography.nngla_source_artifact",
    "geography.nngla_spatial_feature",
    "geography.nngla_geometry_version",
    "geography.nngla_geometry_authority_record",
    "geography.nngla_canonical_crosswalk",
    "geography.nngla_execution_receipt",
    "geography.nngla_execution_item",
    "geography.nngla_place_reference",
    "geography.nngla_administrative_area",
    "geography.nngla_road",
    "geography.nngla_address",
    "geography.nngla_parcel",
    "geography.nngla_title",
    "geography.nngla_state_land",
    "geography.nngla_survey_control_point",
    "geography.nngla_road_segment",
    "geography.nngla_title_reference_reservation",
    "geography.nngla_parcel_reference_reservation",
    "geography.nngla_geometry_change_candidate",
    "geography.nngla_feature_runtime_candidate",
    "geography.nngla_name_id_reservation",
    "geography.nngla_runtime_command_receipt",
    "geography.nngla_spatial_read_projection_v1",
)

REQUIRED_FUNCTIONS = (
    "nngla_reserve_address_number",
    "nngla_reserve_title_reference",
    "nngla_reserve_parcel_reference",
    "nngla_reserve_geometry_id",
    "nngla_reserve_feature_id",
    "nngla_reserve_name_id",
    "nngla_claim_runtime_command",
    "nngla_reverse_geocode",
)


def _relation_status(connection) -> dict[str, bool]:
    out: dict[str, bool] = {}
    with connection.cursor() as cur:
        for relation in REQUIRED_RELATIONS:
            cur.execute("SELECT to_regclass(%s) IS NOT NULL", (relation,))
            out[relation] = bool(cur.fetchone()[0])
    return out


def _function_status(connection) -> dict[str, bool]:
    out: dict[str, bool] = {}
    with connection.cursor() as cur:
        for name in REQUIRED_FUNCTIONS:
            cur.execute(
                "SELECT EXISTS(SELECT 1 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='geography' AND p.proname=%s)",
                (name,),
            )
            out[f"geography.{name}"] = bool(cur.fetchone()[0])
    return out


def _target_metadata(connection) -> tuple[str, str, bool]:
    with connection.cursor() as cur:
        cur.execute("SELECT current_database(), current_user")
        database_name, current_user = map(str, cur.fetchone())
        cur.execute(
            "SELECT COALESCE((SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()), false)"
        )
        ssl_enabled = bool(cur.fetchone()[0])
    return database_name, current_user, ssl_enabled


def _migration_ledger_state(connection) -> tuple[int, int, tuple[str, ...], tuple[str, ...]]:
    with connection.cursor() as cur:
        cur.execute("SELECT to_regclass('platform.schema_migration') IS NOT NULL")
        if not bool(cur.fetchone()[0]):
            return 0, 1, REQUIRED_MIGRATION_IDS, ()
        cur.execute("SELECT migration_id,status FROM platform.schema_migration")
        rows = {str(migration_id): str(status) for migration_id, status in cur.fetchall()}
    applied = sum(1 for status in rows.values() if status == "APPLIED")
    non_applied = sum(1 for status in rows.values() if status != "APPLIED")
    missing = tuple(migration_id for migration_id in REQUIRED_MIGRATION_IDS if migration_id not in rows)
    wrong = tuple(
        migration_id for migration_id in REQUIRED_MIGRATION_IDS
        if migration_id in rows and rows[migration_id] != "APPLIED"
    )
    return applied, non_applied, missing, wrong


def inspect_preflight(root: Path, connection, environment_name: str) -> TargetPreflight:
    database_name, current_user, ssl_enabled = _target_metadata(connection)
    relations = _relation_status(connection)
    functions = _function_status(connection)
    applied, non_applied, missing_migrations, non_applied_required = _migration_ledger_state(connection)
    empty = assess_empty_registers(root, connection)
    candidate = assess_candidate_state(root)
    baseline = verify_immutable_baseline(root, connection)

    findings: list[str] = []
    if applied < 18 or non_applied != 0 or missing_migrations or non_applied_required:
        findings.append(f"MIGRATION_LEDGER_REQUIRED_BASELINE_NOT_APPLIED:{applied}:{non_applied}")
    findings.extend(f"REQUIRED_MIGRATION_MISSING:{value}" for value in missing_migrations)
    findings.extend(f"REQUIRED_MIGRATION_NOT_APPLIED:{value}" for value in non_applied_required)
    findings.extend(f"RELATION_MISSING:{key}" for key, value in relations.items() if not value)
    findings.extend(f"FUNCTION_MISSING:{key}" for key, value in functions.items() if not value)
    if not bundle17e_is_qualified():
        findings.append("BUNDLE17E_OFFLINE_QUALIFICATION_FAILED")
    if not empty_registers_ready(empty):
        findings.append("EMPTY_REGISTER_READINESS_FAILED")
    if not candidate.passed:
        findings.extend(candidate.findings or ("CANDIDATE_STATE_READINESS_FAILED",))
    if not baseline.passed:
        findings.append("IMMUTABLE_BASELINE_RECONCILIATION_FAILED")

    return TargetPreflight(
        database_name=database_name,
        environment_name=environment_name,
        current_user=current_user,
        ssl_enabled=ssl_enabled,
        migration_ledger_applied=applied,
        migration_ledger_non_applied=non_applied,
        required_migrations_missing=missing_migrations,
        required_migrations_non_applied=non_applied_required,
        required_relations=relations,
        required_functions=functions,
        bundle17e_qualified=bundle17e_is_qualified(),
        empty_registers_ready=empty_registers_ready(empty),
        candidate_state_ready=candidate.passed,
        immutable_baseline_ready=baseline.passed,
        findings=tuple(findings),
    )


__all__ = [
    "REQUIRED_MIGRATION_IDS",
    "REQUIRED_RELATIONS",
    "REQUIRED_FUNCTIONS",
    "inspect_preflight",
]
