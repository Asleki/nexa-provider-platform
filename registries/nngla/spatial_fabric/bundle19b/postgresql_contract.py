"""Existing PostgreSQL/PostGIS capabilities reused by Bundle 19B without migration."""
from __future__ import annotations
from ._shared import ROOT
PLACE_ADMIN_SQL=ROOT/'database'/'migrations'/'m006_07_11_nngla_identity_places_runtime.sql'
EXECUTION_SQL=ROOT/'database'/'migrations'/'m006_07_11_nngla_execution_foundation.sql'
GEOMETRY_SQL=ROOT/'database'/'migrations'/'m006_07_11_nngla_geometry_roads_runtime.sql'
CHANGE_SQL=ROOT/'database'/'migrations'/'m006_07_11_nngla_geometry_change_lifecycle.sql'
WORLD_SQL=ROOT/'database'/'migrations'/'m004_01_02_world_geometry_authority.sql'
REQUIRED_RELATIONS=('geography.world_boundary_version','geography.nngla_place_reference','geography.nngla_administrative_area','geography.nngla_geometry_version','geography.nngla_geometry_authority_record','geography.nngla_geometry_id_reservation','geography.nngla_execution_receipt','geography.nngla_execution_item')
def existing_schema_findings():
    texts=[p.read_text(encoding='utf-8').lower() for p in (PLACE_ADMIN_SQL,EXECUTION_SQL,GEOMETRY_SQL,CHANGE_SQL,WORLD_SQL)]
    joined='\n'.join(texts); required=('create table geography.nngla_administrative_area','geometry_reference text','create table geography.nngla_geometry_version','create table geography.nngla_geometry_authority_record','create table geography.nngla_geometry_id_reservation','nngla_reserve_geometry_id','create table geography.nngla_execution_receipt','create table geography.world_boundary_version')
    return tuple('missing-existing-capability:'+x for x in required if x not in joined)
def bundle19b_requires_schema_migration(): return False
