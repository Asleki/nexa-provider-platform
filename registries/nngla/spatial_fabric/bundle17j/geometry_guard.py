from __future__ import annotations
import re
from ._shared import BASE_GEOMETRY_PATH,GEOMETRY_ASSIGNMENT_PATH,csv_rows
_GEO=re.compile(r'^NG-GEO-(\d{6})$')
def occupied_geometry_ids():
    ids={r.get('geometry_id') or r.get('geometry_version_candidate_id') for r in csv_rows(BASE_GEOMETRY_PATH)}
    ids.update(r['geometry_id'] for r in csv_rows(GEOMETRY_ASSIGNMENT_PATH))
    return tuple(sorted(ids,key=lambda x:int(x.rsplit('-',1)[1])))
def geometry_namespace_baseline():
    ids=occupied_geometry_ids(); nums=[int(_GEO.fullmatch(x).group(1)) for x in ids]
    return {'occupied_count':len(set(ids)),'max_geometry_id':f'NG-GEO-{max(nums):06d}','next_candidate_id':f'NG-GEO-{max(nums)+1:06d}','collision_free':len(ids)==len(set(ids))}
__all__=['occupied_geometry_ids','geometry_namespace_baseline']
