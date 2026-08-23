"""PostgreSQL capabilities required/introduced by P006.7.11.12."""
from __future__ import annotations
from ._shared import ROOT

EXISTING_SQL = ROOT / "database" / "migrations" / "m006_07_11_nngla_geometry_roads_runtime.sql"
NETWORK_SQL = ROOT / "database" / "migrations" / "m006_07_11_nngla_road_network_construction.sql"
REQUIRED_EXISTING = ("geography.nngla_road", "geography.nngla_road_reference_candidate", "geography.nngla_geometry_version")
REQUIRED_NEW = ("geography.nngla_road_network_node", "geography.nngla_road_network_connection")

def schema_findings() -> tuple[str,...]:
    old = EXISTING_SQL.read_text(encoding="utf-8").lower()
    new = NETWORK_SQL.read_text(encoding="utf-8").lower() if NETWORK_SQL.exists() else ""
    out=[]
    for token in ("create table geography.nngla_road_reference_candidate", "create table geography.nngla_road"):
        if token not in old: out.append("missing-existing:"+token)
    for token in ("create table geography.nngla_road_network_node", "create table geography.nngla_road_network_connection"):
        if token not in new: out.append("missing-new:"+token)
    return tuple(out)
