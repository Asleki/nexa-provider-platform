from dataclasses import replace
from pathlib import Path

from registries.nngla.spatial_realization.closure import build_city_closure
from registries.nngla.spatial_realization.contracts import GeometryEncoding
from registries.nngla.spatial_realization.persistence import PostgreSQLSpatialRealizationRepository


class _Cursor:
    def __init__(self):self.calls=[]
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def execute(self,sql,params=()):
        assert sql.count('%s')==len(params), f'placeholder mismatch: {sql.count("%s")} != {len(params)}'
        self.calls.append((sql,params))
    def fetchone(self):return ('NG-GEO-999999',)


class _Connection:
    def __init__(self):self.cursor_obj=_Cursor()
    def cursor(self):return self.cursor_obj


def test_postgresql_geometry_insert_sql_binds_every_placeholder_for_geojson_and_ewkb():
    connection=_Connection();repo=PostgreSQLSpatialRealizationRepository(connection,environment_name='dev')
    candidate=build_city_closure('NG-PLC-000001').place_reference
    repo.persist_geometry(candidate,'NG-GEO-900001')
    ewkb=replace(candidate,encoding=GeometryEncoding.EWKB_HEX,payload='0101000020e610000000000000000000000000000000000000',checksum_sha256='f'*64)
    repo.persist_geometry(ewkb,'NG-GEO-900002')
    assert len(connection.cursor_obj.calls)==4


def test_existing_schema_sources_cover_every_relation_used_by_spatial_realization():
    corpus='\n'.join(path.read_text(errors='ignore').lower() for path in Path('database').rglob('*.sql'))
    for token in (
        'nngla_place_reference','nngla_administrative_area','nngla_geometry_authority_record',
        'nngla_geometry_version','nngla_geometry_id_reservation','nngla_geometry_supersession_link',
        'nngla_execution_receipt','nngla_execution_item','world_boundary_version','nngla_reserve_geometry_id',
    ):
        assert token in corpus
