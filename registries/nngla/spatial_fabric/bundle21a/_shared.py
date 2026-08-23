"""Shared paths/constants for P006.7.11.14 / Bundle 21A."""
from __future__ import annotations
from csv import DictReader
from hashlib import sha256
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[4]
SPATIAL_ROOT=ROOT/'data'/'novegeo'/'nngla'/'spatial-fabric'; BUNDLE_ROOT=SPATIAL_ROOT/'bundle21a'; CONTROL_ROOT=BUNDLE_ROOT/'controlled'; PUBLICATION_ROOT=BUNDLE_ROOT/'publication'; PROJECTION_ROOT=BUNDLE_ROOT/'projection'; EVIDENCE_ROOT=BUNDLE_ROOT/'evidence'
PLACE_POINTS=SPATIAL_ROOT/'bundle19a'/'qualified'/'novegeo_place_reference_points_v001.csv'
SETTLEMENT_NAMES=ROOT/'data'/'novegeo'/'nngla'/'geographic-identity-places'/'source'/'04_name_catalogues'/'settlement_name_catalogue.csv'
ADMIN_BOUNDARIES=SPATIAL_ROOT/'bundle19b'/'qualified'/'novegeo_administrative_boundaries_v001.geojson'
ROAD_ALIGNMENTS=SPATIAL_ROOT/'bundle20a'/'qualified'/'novegeo_road_alignments_v001.geojson'
FEATURE_NAMES=SPATIAL_ROOT/'bundle20b'/'naming'/'novegeo_physical_feature_geographic_names_v001.csv'
CANONICAL_ALIGNMENT=SPATIAL_ROOT/'source'/'08_relationships'/'novegeo_existing_canonical_alignment_v002.csv'
POLICY=CONTROL_ROOT/'novegeo_spatial_publication_policy_v001.csv'
CANDIDATES=PUBLICATION_ROOT/'novegeo_spatial_publication_candidates_v001.csv'
DECISIONS=PUBLICATION_ROOT/'novegeo_spatial_publication_decisions_v001.csv'
PROJECTION_CANDIDATES=PROJECTION_ROOT/'novegeo_national_read_projection_candidates_v001.csv'
QUALIFICATION=EVIDENCE_ROOT/'novegeo_spatial_publication_qualification_v001.csv'
SOURCE_HASHES=EVIDENCE_ROOT/'novegeo_spatial_publication_source_hashes_v001.csv'
SUMMARY=EVIDENCE_ROOT/'novegeo_spatial_publication_summary_v001.json'
BUNDLE_CODE='P006.7.11.14'; BUNDLE_NAME='Governed Spatial Publication and National Read Projection'; BUNDLE_EFFECTIVE_DATE='2026-08-23'; TARGET_RUNTIME='simulation'; EFFECT_SCOPE='SHARED_REFERENCE'; READ_MODEL_VERSION=1

def csv_rows(path):
    with Path(path).open('r',encoding='utf-8-sig',newline='') as h:return tuple(dict(r) for r in DictReader(h))
def json_payload(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def stable_hash(*parts):return sha256('\x1f'.join(str(p) for p in parts).encode()).hexdigest()
def stable_id(prefix,*parts):return prefix+stable_hash(*parts)
def sha256_path(path):return sha256(Path(path).read_bytes()).hexdigest()
INPUT_PATHS=(PLACE_POINTS,SETTLEMENT_NAMES,ADMIN_BOUNDARIES,ROAD_ALIGNMENTS,FEATURE_NAMES,CANONICAL_ALIGNMENT,POLICY)
