from ._shared import ROOT
NAME_SQL=ROOT/'database'/'migrations'/'m006_07_11_nngla_geographic_naming_gazette.sql'
NETWORK_SQL=ROOT/'database'/'migrations'/'m006_07_11_nngla_road_network_construction.sql'
def schema_findings():
    n=NAME_SQL.read_text().lower(); r=NETWORK_SQL.read_text().lower(); out=[]
    for t in ('geography.nngla_geographic_name','geography.nngla_name_assignment'):
        if t not in n: out.append('missing:'+t)
    if 'geography.nngla_spatial_relationship_evidence' not in r: out.append('missing:relationship-evidence')
    return tuple(out)
