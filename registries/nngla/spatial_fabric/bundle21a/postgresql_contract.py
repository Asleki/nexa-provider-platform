from ._shared import ROOT
READ_SQL=ROOT/'database'/'migrations'/'m006_07_11_nngla_spatial_query_read_models.sql'; PUB_SQL=ROOT/'database'/'migrations'/'m006_07_11_nngla_governed_spatial_publication.sql'
def schema_findings():
    r=READ_SQL.read_text().lower(); p=PUB_SQL.read_text().lower() if PUB_SQL.exists() else ''; out=[]
    if 'create table geography.nngla_spatial_read_projection_v1' not in r: out.append('missing-existing-projection')
    if "visibility <> 'public' or publication_reference is not null" not in r: out.append('missing-publication-reference-guard')
    if 'create table geography.nngla_publication_record' not in p: out.append('missing-durable-publication-ledger')
    return tuple(out)
