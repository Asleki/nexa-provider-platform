"""Shared paths/constants for P006.7.11.13 / Bundle 20B."""
from __future__ import annotations
from csv import DictReader
from hashlib import sha256
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[4]
SPATIAL_ROOT=ROOT/'data'/'novegeo'/'nngla'/'spatial-fabric'
BUNDLE_ROOT=SPATIAL_ROOT/'bundle20b'; QUALIFIED_ROOT=BUNDLE_ROOT/'qualified'; RELATIONSHIP_ROOT=BUNDLE_ROOT/'relationships'; NAMING_ROOT=BUNDLE_ROOT/'naming'; EVIDENCE_ROOT=BUNDLE_ROOT/'evidence'
HYDROLOGY=ROOT/'data'/'novegeo'/'geography'/'hydrology'/'qualified'/'novegeo_hydrology_v001.json'
TERRAIN=ROOT/'data'/'novegeo'/'geography'/'terrain'/'qualified'/'novegeo_terrain_v001.json'
LANDFORMS=SPATIAL_ROOT/'source'/'02_existing_physical_world'/'novegeo_landform_reference_points_v001.csv'
FEATURE_NAMES=ROOT/'data'/'novegeo'/'nngla'/'geographic-identity-places'/'source'/'08_relationships'/'feature_name_assignment_candidates.csv'
NAME_RESULTS=ROOT/'data'/'novegeo'/'nngla'/'geographic-identity-places'/'source'/'10_evidence'/'novegeo_name_assignment_results_v001.csv'
CANONICAL_ALIGNMENT=SPATIAL_ROOT/'source'/'08_relationships'/'novegeo_existing_canonical_alignment_v002.csv'
ROAD_RELATIONSHIPS=SPATIAL_ROOT/'bundle20a'/'relationships'/'novegeo_road_spatial_relationships_v001.csv'
HYDRO_RELATIONSHIPS=RELATIONSHIP_ROOT/'novegeo_hydrographic_relationships_v001.csv'
LANDFORM_EXTENTS=QUALIFIED_ROOT/'novegeo_landform_extent_candidates_v001.geojson'
GEOGRAPHIC_NAMES=NAMING_ROOT/'novegeo_physical_feature_geographic_names_v001.csv'
NAME_ASSIGNMENTS=NAMING_ROOT/'novegeo_physical_feature_name_assignments_v001.csv'
QUALIFICATION=EVIDENCE_ROOT/'novegeo_hydrology_landforms_naming_qualification_v001.csv'
SOURCE_HASHES=EVIDENCE_ROOT/'novegeo_hydrology_landforms_naming_source_hashes_v001.csv'
SUMMARY=EVIDENCE_ROOT/'novegeo_hydrology_landforms_naming_summary_v001.json'
BUNDLE_CODE='P006.7.11.13'; BUNDLE_NAME='Hydrology, Landforms and Geographic Naming'; BUNDLE_EFFECTIVE_DATE='2026-08-23'; RUNTIME_MODE='production'; EFFECT_SCOPE='SHARED_REFERENCE'; CRS_CODE='NG-CRS-EPSG4326'

def csv_rows(path):
    with Path(path).open('r',encoding='utf-8-sig',newline='') as h:return tuple(dict(r) for r in DictReader(h))
def json_payload(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def stable_hash(*parts):return sha256('\x1f'.join(str(p) for p in parts).encode()).hexdigest()
def stable_id(prefix,*parts):return prefix+stable_hash(*parts)
def sha256_path(path):return sha256(Path(path).read_bytes()).hexdigest()
INPUT_PATHS=(HYDROLOGY,TERRAIN,LANDFORMS,FEATURE_NAMES,NAME_RESULTS,CANONICAL_ALIGNMENT,ROAD_RELATIONSHIPS)
