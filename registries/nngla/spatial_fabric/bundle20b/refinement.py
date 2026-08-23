"""Hydrology relationships and evidence-derived optional landform extents."""
from __future__ import annotations
from math import hypot

from registries.nngla.spatial_fabric.bundle20a.geometry import convex_hull
from ._shared import *
from .contracts import HydroRelationship, LandformExtentCandidate
from .source import subject_to_alignment


def hydro_relationships():
    h = json_payload(HYDROLOGY); aligned = subject_to_alignment(); out = []
    for r in h['rivers']:
        a = aligned[r['riverId']]; fid = a['canonical_id']
        out.append(HydroRelationship(stable_id('hydrorel:nngla:', fid, 'NETWORK', r['drainageNetworkId']), fid, r['riverId'], 'MEMBER_OF_DRAINAGE_NETWORK', r['drainageNetworkId'], 'QUALIFIED_HYDROLOGY_V001'))
        if r.get('outletType') == 'coast':
            out.append(HydroRelationship(stable_id('hydrorel:nngla:', fid, 'COAST'), fid, r['riverId'], 'FLOWS_TO_COAST', 'coast:novegeo', 'QUALIFIED_HYDROLOGY_OUTLET'))
    byriver = {r['riverId']: aligned[r['riverId']]['canonical_id'] for r in h['rivers']}
    for j in h['junctions']:
        recv = j['receivingRiverId']; fid = byriver[recv]
        for incoming in j['incomingRiverIds']:
            out.append(HydroRelationship(stable_id('hydrorel:nngla:', fid, 'TRIBUTARY', incoming, j['junctionId']), fid, recv, 'RECEIVES_TRIBUTARY_AT', incoming, f"{j['junctionId']}@{j['coordinate']['longitude']},{j['coordinate']['latitude']}"))
    for l in h['lakes']:
        a = aligned[l['lakeId']]; fid = a['canonical_id']
        out.append(HydroRelationship(stable_id('hydrorel:nngla:', fid, 'NETWORK', l['drainageNetworkId']), fid, l['lakeId'], 'MEMBER_OF_DRAINAGE_NETWORK', l['drainageNetworkId'], 'QUALIFIED_HYDROLOGY_V001'))
        if l.get('hydrologicRole') == 'closed_basin_lake':
            out.append(HydroRelationship(stable_id('hydrorel:nngla:', fid, 'CLOSED'), fid, l['lakeId'], 'CLOSED_BASIN', l['drainageNetworkId'], 'QUALIFIED_HYDROLOGY_CLOSED_BASIN'))
    # Carry road crossings forward without claiming bridges.
    if ROAD_RELATIONSHIPS.exists():
        subject_to_fid = {k: v['canonical_id'] for k, v in aligned.items()}
        for rr in csv_rows(ROAD_RELATIONSHIPS):
            if rr['relationship_type'] == 'CROSSES_RIVER' and rr['object_id'] in subject_to_fid:
                fid = subject_to_fid[rr['object_id']]
                out.append(HydroRelationship(stable_id('hydrorel:nngla:', fid, 'ROAD', rr['road_id']), fid, rr['object_id'], 'CROSSED_BY_ROAD', rr['road_id'], 'BUNDLE20A_GEOMETRIC_CROSSING_NOT_BRIDGE_ASSERTION'))
    return tuple(sorted(out, key=lambda x: x.relationship_id))


def landform_extents():
    terrain = json_payload(TERRAIN)['samples']; aligned = subject_to_alignment(); rows = csv_rows(LANDFORMS); out = []
    for r in rows:
        lon = float(r['longitude']); lat = float(r['latitude']); radius = float(r['influence_radius_degrees']); cls = r['landform_type'].lower()
        candidates = []
        for s in terrain:
            if str(s['landformClass']).lower() != cls:
                continue
            d = hypot(float(s['longitude']) - lon, float(s['latitude']) - lat)
            if d <= radius * 1.35:
                candidates.append((d, (float(s['longitude']), float(s['latitude']))))
        candidates.sort(); pts = [p for _, p in candidates[:18]]
        if len(pts) < 3:
            continue
        ring = convex_hull(pts + [(lon, lat)])
        if len(ring) < 4:
            continue
        a = aligned[r['landform_reference_id']]
        out.append(LandformExtentCandidate(a['canonical_id'], r['landform_reference_id'], a['geometry_id'], r['landform_type'], ring, len(pts), f"p006.7.11.13:landform-extent:{a['canonical_id']}", 'QUALIFIED_TERRAIN_V001_OBSERVATIONAL_CONVEX_HULL'))
    return tuple(out)
