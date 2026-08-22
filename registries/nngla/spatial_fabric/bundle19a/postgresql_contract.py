"""Existing PostgreSQL/PostGIS capabilities consumed by Bundle 19A without schema replacement."""
from __future__ import annotations

from ._shared import ROOT

WORLD_GEOMETRY_SQL = ROOT / "database" / "migrations" / "m004_01_02_world_geometry_authority.sql"
PLACE_RUNTIME_SQL = ROOT / "database" / "migrations" / "m006_07_11_nngla_identity_places_runtime.sql"
EXECUTION_FOUNDATION_SQL = ROOT / "database" / "migrations" / "m006_07_11_nngla_execution_foundation.sql"
GEOMETRY_RUNTIME_SQL = ROOT / "database" / "migrations" / "m006_07_11_nngla_geometry_roads_runtime.sql"
GEOMETRY_CHANGE_SQL = ROOT / "database" / "migrations" / "m006_07_11_nngla_geometry_change_lifecycle.sql"

REQUIRED_RELATIONS = (
    "geography.world_boundary_version",
    "geography.nngla_place_reference",
    "geography.nngla_geometry_version",
    "geography.nngla_geometry_authority_record",
    "geography.nngla_geometry_id_reservation",
    "geography.nngla_execution_receipt",
    "geography.nngla_execution_item",
)


def existing_schema_findings() -> tuple[str, ...]:
    findings: list[str] = []
    texts = {
        "world": WORLD_GEOMETRY_SQL.read_text(encoding="utf-8").lower(),
        "place": PLACE_RUNTIME_SQL.read_text(encoding="utf-8").lower(),
        "execution": EXECUTION_FOUNDATION_SQL.read_text(encoding="utf-8").lower(),
        "geometry": GEOMETRY_RUNTIME_SQL.read_text(encoding="utf-8").lower(),
        "change": GEOMETRY_CHANGE_SQL.read_text(encoding="utf-8").lower(),
    }
    required = {
        "world": ("create table geography.world_boundary_version", "geometry geometry(multipolygon, 4326)", "st_isvalid"),
        "place": ("create table geography.nngla_place_reference", "spatial_assignment_status", "geometry_reference"),
        "execution": ("create table geography.nngla_geometry_version", "create table geography.nngla_execution_receipt", "create table geography.nngla_execution_item"),
        "geometry": ("create table geography.nngla_geometry_authority_record", "geometry_role_code", "runtime_effect_scope"),
        "change": ("create table geography.nngla_geometry_id_reservation", "create or replace function geography.nngla_reserve_geometry_id", "for update"),
    }
    for family, tokens in required.items():
        for token in tokens:
            if token not in texts[family]:
                findings.append(f"missing-existing-capability:{family}:{token}")
    return tuple(findings)


def bundle19a_requires_schema_migration() -> bool:
    """False by design: Bundle 19A consumes locked generic geometry/place infrastructure additively."""
    return False


__all__ = [
    "WORLD_GEOMETRY_SQL", "PLACE_RUNTIME_SQL", "EXECUTION_FOUNDATION_SQL", "GEOMETRY_RUNTIME_SQL",
    "GEOMETRY_CHANGE_SQL", "REQUIRED_RELATIONS", "existing_schema_findings", "bundle19a_requires_schema_migration",
]
