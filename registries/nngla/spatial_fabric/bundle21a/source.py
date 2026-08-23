"""Build current publication candidates from predecessor bundle artifacts."""
from __future__ import annotations
from ._shared import *
from .contracts import PublicationCandidate

def current_candidates():
    out=[]
    name_by_source={r['source_place_code']:r for r in csv_rows(SETTLEMENT_NAMES)}
    for p in csv_rows(PLACE_POINTS):
        n=name_by_source[p['source_place_code']]
        out.append(PublicationCandidate(p['place_id'],'PLACE',p['canonical_name'],p['geometry_id'],n['naming_status_code'],p['spatial_assignment_status'],'','NOT_PUBLISHED'))
    for f in json_payload(ADMIN_BOUNDARIES)['features']:
        p=f['properties']; out.append(PublicationCandidate(p['administrative_area_id'],'ADMINISTRATIVE_AREA',p['canonical_name'],p['geometry_id'],'GAZETTED' if p['resulting_lifecycle_status']=='ACTIVE' else 'PROPOSED',p['resulting_lifecycle_status'],p['resulting_boundary_status'],'NOT_PUBLISHED'))
    for f in json_payload(ROAD_ALIGNMENTS)['features']:
        p=f['properties']; out.append(PublicationCandidate(p['road_id'],'ROAD',p['canonical_name'],p['geometry_id'],'PROPOSED','OPERATIONAL_MAPPED','AUTHORITATIVELY_MAPPED','NOT_PUBLISHED'))
    align={r['canonical_id']:r for r in csv_rows(CANONICAL_ALIGNMENT) if r['object_family']=='GEOGRAPHIC_FEATURE'}
    for n in csv_rows(FEATURE_NAMES):
        a=align[n['feature_id']]; out.append(PublicationCandidate(n['feature_id'],'GEOGRAPHIC_FEATURE',n['canonical_name'],a['geometry_id'],n['naming_status_code'],'ACTIVE','QUALIFIED','SOURCE_AVAILABLE'))
    return tuple(out)

def source_hashes(): return tuple((str(p.relative_to(ROOT)),sha256_path(p)) for p in INPUT_PATHS if p.exists())
