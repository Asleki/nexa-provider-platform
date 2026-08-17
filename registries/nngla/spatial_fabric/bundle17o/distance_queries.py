"""Reference distance/nearest calculations; Production authority remains PostGIS."""
from __future__ import annotations
from math import asin,cos,radians,sin,sqrt
from .contracts import DistanceMeasurement, SpatialReadRecord

EARTH_RADIUS_M=6371008.8
def geodesic_distance_meters(lon1,lat1,lon2,lat2):
    p1,p2=radians(lat1),radians(lat2); dp=radians(lat2-lat1); dl=radians(lon2-lon1)
    a=sin(dp/2)**2+cos(p1)*cos(p2)*sin(dl/2)**2
    return 2*EARTH_RADIUS_M*asin(sqrt(a))
def distance_between(a: SpatialReadRecord,b: SpatialReadRecord) -> DistanceMeasurement:
    if None in (a.longitude,a.latitude,b.longitude,b.latitude): raise ValueError("reference adapter requires point/centroid coordinates")
    return DistanceMeasurement(a.subject_id,b.subject_id,geodesic_distance_meters(a.longitude,a.latitude,b.longitude,b.latitude),"m","WGS84_GEODESIC_REFERENCE","EPSG:4326","NG-CRS-EPSG4326")
def nearest(origin: SpatialReadRecord,candidates,*,limit=1):
    ranked=sorted(((distance_between(origin,c),c) for c in candidates if c.subject_id!=origin.subject_id),key=lambda x:x[0].distance_value)
    return tuple(x[0] for x in ranked[:limit])
__all__=["EARTH_RADIUS_M","geodesic_distance_meters","distance_between","nearest"]
