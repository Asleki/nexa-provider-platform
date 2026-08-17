"""PostGIS query/read contract; additive, visibility-governed and host agnostic."""
from ._shared import SCHEMA_PATH
def load_schema17o_sql(): return SCHEMA_PATH.read_text(encoding="utf-8")
def qualify_schema17o_sql(sql):
    n=sql.lower(); compact="".join(n.split()); findings=[]
    for token in (
        "create table geography.nngla_spatial_read_projection_v1",
        "create or replace view geography.nngla_spatial_subject_read_v1",
        "create or replace function geography.nngla_current_geometry",
        "st_contains","st_covers","st_within","st_coveredby","st_intersects","st_crosses","st_touches",
        "st_distance","<->","nngla_road_frontage","nngla_query_fronts","nngla_reverse_geocode",
        "nngla_geographic_name","nngla_name_assignment","publication_reference",
    ):
        if token not in n: findings.append("missing-sql:"+token)
    if "wherep.visibility='public'" not in compact:
        findings.append("missing-sql:public-projection-filter")
    if "check(visibility<>'public'orpublication_referenceisnotnull)" not in compact:
        findings.append("missing-sql:public-publication-reference-check")
    for bad in ("nexaecosystem.com","localhost","namecheap","password"):
        if bad in n: findings.append("forbidden-coupling:"+bad)
    for verb in ("insert into geography.nngla_spatial_feature","update geography.nngla_spatial_feature","delete from geography.nngla_spatial_feature"):
        if verb in n: findings.append("query-contract-canonical-mutation")
    return tuple(findings)
__all__=["load_schema17o_sql","qualify_schema17o_sql"]
