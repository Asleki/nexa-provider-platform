"""Shared constants/helpers for P006.7.11.11 / Bundle 19B."""
from __future__ import annotations
from csv import DictReader
from hashlib import sha256
from pathlib import Path
import json

ROOT=Path(__file__).resolve().parents[4]
SPATIAL_ROOT=ROOT/'data'/'novegeo'/'nngla'/'spatial-fabric'
BUNDLE19A_ROOT=SPATIAL_ROOT/'bundle19a'
BUNDLE_ROOT=SPATIAL_ROOT/'bundle19b'
CONTROL_ROOT=BUNDLE_ROOT/'controlled'
QUALIFIED_ROOT=BUNDLE_ROOT/'qualified'
RELATIONSHIP_ROOT=BUNDLE_ROOT/'relationships'
LEGALIZATION_ROOT=BUNDLE_ROOT/'legalization'
EVIDENCE_ROOT=BUNDLE_ROOT/'evidence'
ADMIN_SOURCE=ROOT/'data'/'novegeo'/'nngla'/'geographic-identity-places'/'source'/'05_geographic_candidates'/'administrative_area_candidates.csv'
CANONICAL_ALIGNMENT=SPATIAL_ROOT/'source'/'08_relationships'/'novegeo_existing_canonical_alignment_v002.csv'
BOUNDARY_REQUESTS=SPATIAL_ROOT/'source'/'04_settlements_roads_administration'/'novegeo_administrative_boundary_candidates_v001.csv'
PLACE_POINTS=BUNDLE19A_ROOT/'qualified'/'novegeo_place_reference_points_v001.csv'
PLACE_FOOTPRINTS=BUNDLE19A_ROOT/'qualified'/'novegeo_settlement_footprints_v001.geojson'
SOVEREIGN_GEOJSON=ROOT/'data'/'novegeo'/'geography'/'world-boundary'/'candidate'/'novegeo_world_boundary_v002.geojson'
TOPOLOGY_POLICY=CONTROL_ROOT/'novegeo_administrative_topology_policy_v001.csv'
BOUNDARIES=QUALIFIED_ROOT/'novegeo_administrative_boundaries_v001.geojson'
TOPOLOGY_RELATIONSHIPS=RELATIONSHIP_ROOT/'novegeo_administrative_topology_relationships_v001.csv'
ASSIGNMENTS=RELATIONSHIP_ROOT/'novegeo_effective_dated_administrative_geometry_assignments_v001.csv'
LEGALIZATION_DECISIONS=LEGALIZATION_ROOT/'novegeo_administrative_boundary_legalization_decisions_v001.csv'
QUALIFICATION_RESULTS=EVIDENCE_ROOT/'novegeo_administrative_boundary_qualification_results_v001.csv'
SOURCE_HASHES=EVIDENCE_ROOT/'novegeo_administrative_boundary_source_hashes_v001.csv'
SUMMARY=EVIDENCE_ROOT/'novegeo_administrative_boundary_summary_v001.json'
BUNDLE_CODE='P006.7.11.11'
BUNDLE_NAME='Administrative Boundary Authoring and Legalization'
BUNDLE_VERSION=1
BUNDLE_EFFECTIVE_DATE='2026-08-22'
RUNTIME_MODE='production'
EFFECT_SCOPE='SHARED_REFERENCE'
CRS_CODE='NG-CRS-EPSG4326'
GEOMETRY_ROLE='ADMINISTRATIVE_BOUNDARY'
DATASET_ID='dataset:novegeo:administrative-boundaries'
DATASET_VERSION='1'
SOVEREIGN_BOUNDARY_ID='boundary:novegeo:sovereign'
SOVEREIGN_BOUNDARY_VERSION=2
EXPECTED_TYPE_COUNTS={'TOWNSHIP':72,'CITY_DISTRICT':64,'MUNICIPALITY':24,'INDUSTRIAL_ZONE':16,'CITY':8,'REGION':8}
EXPECTED_COUNT=192
INPUT_PATHS=(ADMIN_SOURCE,CANONICAL_ALIGNMENT,BOUNDARY_REQUESTS,PLACE_POINTS,PLACE_FOOTPRINTS,SOVEREIGN_GEOJSON,TOPOLOGY_POLICY)

def csv_rows(path:Path):
    with Path(path).open('r',encoding='utf-8-sig',newline='') as h:return tuple(dict(r) for r in DictReader(h))
def json_payload(path:Path): return json.loads(Path(path).read_text(encoding='utf-8'))
def sha256_path(path:Path): return sha256(Path(path).read_bytes()).hexdigest()
def stable_hash(*parts:object): return sha256('\x1f'.join(str(x) for x in parts).encode()).hexdigest()
def stable_id(prefix:str,*parts:object): return prefix+stable_hash(*parts)
def payload_sha256(payload:object):return sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False,default=str).encode()).hexdigest()
