from collections import Counter
from .refinement import hydro_relationships,landform_extents
from .naming import physical_feature_names

def qualify_bundle():
    out=[]; names=physical_feature_names(); ext=landform_extents(); hydro=hydro_relationships()
    if len(names)!=20: out.append('NAME_COUNT')
    if Counter(n.name_family for n in names)!=Counter({'RIVER':5,'LAKE':3,'MOUNTAIN':3,'VALLEY':3,'PLAIN':3,'PLATEAU':3}): out.append('NAME_FAMILIES')
    if any(n.official_effect or n.naming_status_code!='PROPOSED' for n in names): out.append('AUTO_GAZETTE')
    if len(ext)!=11: out.append(f'LANDFORM_EXTENT_COUNT:{len(ext)}')
    if not hydro: out.append('NO_HYDRO_RELATIONSHIPS')
    return tuple(out)
