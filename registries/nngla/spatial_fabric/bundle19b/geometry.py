"""Dependency-free GeoJSON helpers used in Bundle 19B static qualification."""
from __future__ import annotations
from registries.nngla.spatial_fabric.bundle19a.geometry import point_relation

def polygon_rings(geometry):
    t=geometry['type']; c=geometry['coordinates']
    if t=='Polygon': return tuple(tuple((float(x),float(y)) for x,y in ring) for ring in c)
    if t=='MultiPolygon': return tuple(tuple((float(x),float(y)) for x,y in ring) for poly in c for ring in poly)
    raise ValueError('polygonal GeoJSON required')
def exterior_rings(geometry):
    if geometry['type']=='Polygon': return (tuple((float(x),float(y)) for x,y in geometry['coordinates'][0]),)
    if geometry['type']=='MultiPolygon': return tuple(tuple((float(x),float(y)) for x,y in poly[0]) for poly in geometry['coordinates'])
    raise ValueError('polygonal GeoJSON required')
def point_covered(point,geometry):
    for ring in exterior_rings(geometry):
        if point_relation(point,ring) in {'INSIDE','BOUNDARY'}: return True
    return False
def all_coordinates(geometry):
    for ring in polygon_rings(geometry):
        for p in ring: yield p
