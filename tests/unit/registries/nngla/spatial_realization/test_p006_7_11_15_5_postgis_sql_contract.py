from registries.nngla.spatial_realization.closure import build_city_closure
from registries.nngla.spatial_realization.contracts import RepairMode
from registries.nngla.spatial_realization.topology import PostGISSpatialTopologyEngine
import re


class _Cursor:
    def __init__(self, connection):
        self.connection=connection;self.sql=''
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def execute(self,sql,params=()):
        assert sql.count('%s')==len(params), f'placeholder mismatch: {sql.count("%s")} != {len(params)}'
        self.sql=sql;self.connection.calls.append((sql,params))
    def fetchall(self):
        sql=self.sql
        if 'R3_FINAL_PARTITION' in sql:
            ids=['__CITY__','NG-ADM-000013','NG-ADM-000014','NG-ADM-000015','NG-ADM-000016','NG-ADM-000017','NG-ADM-000018','NG-ADM-000019','NG-ADM-000020']
            return [(value,'00','POLYGON',8,8,0,0.001) for value in ids]
        if 'ST_IsValid(g.geometry)' in sql and 'outside_geometry' in sql:
            return [
                ('NG-PLC-000001',True,True,4326,'ST_Point',True,True,-1,0.0,0.0,'',''),
                ('NG-PLC-000001',True,True,4326,'ST_Polygon',True,True,-1,0.0,1.0,'',''),
                ('NG-ADM-000001',True,True,4326,'ST_Polygon',True,True,-1,0.0,1000.0,'',''),
                ('NG-ADM-000009',True,True,4326,'ST_Polygon',True,True,-1,0.0,100.0,'',''),
            ]
        if 'canonical_child_seed' in sql or 'WITH seeds(subject_id,longitude,latitude)' in sql:
            return [(f'NG-ADM-{n:06d}',True) for n in range(13,21)]
        return []
    def fetchone(self):
        sql=self.sql
        if sql.strip().startswith('SELECT ST_CoveredBy'):
            return (True,True)
        if 'ST_Difference(child,parent)' in sql and 'ST_Dimension(geom)' in sql:
            return (True,0.0,1000.0,-1,'','')
        if 'peer_overlaps AS' in sql and '(SELECT ST_IsEmpty(geometry) FROM gap)' in sql:
            return (True,0.0,-1,'','',True,0.0,-1,'','',0.0,0,1000.0)
        if 'SELECT ST_IsEmpty((SELECT geometry FROM gap))' in sql:
            return (True,0.0,True,0.0,0,0.0)
        return (True,True)


class _Connection:
    def __init__(self):self.calls=[]
    def cursor(self):return _Cursor(self)


def test_postgis_assessment_sql_binds_all_dynamic_parameters_on_clean_path():
    closure=build_city_closure('NG-PLC-000001')
    connection=_Connection();engine=PostGISSpatialTopologyEngine(connection,repair_mode=RepairMode.DISABLED)
    assessment=engine.assess(closure)
    assert assessment.execution_ready
    assert connection.calls


def test_postgis_successor_repair_sql_binds_all_dynamic_parameters():
    closure=build_city_closure('NG-PLC-000001')
    connection=_Connection();engine=PostGISSpatialTopologyEngine(connection,repair_mode=RepairMode.GOVERNED_STRUCTURAL)
    repaired=engine._repair_selected_fabric(closure,closure.desired_candidates)
    admin=[item for item in repaired if item.geometry_role.value=='ADMINISTRATIVE_BOUNDARY']
    assert len(admin)==9
    assert all(item.is_source_successor for item in admin)


def test_basic_sovereign_sql_qualifies_geometry_columns_across_cross_join():
    closure=build_city_closure('NG-PLC-000001')
    connection=_Connection();engine=PostGISSpatialTopologyEngine(connection,repair_mode=RepairMode.DISABLED)
    engine.assess(closure)
    sql=next(sql for sql,_ in connection.calls if 'outside_geometry' in sql and 'CROSS JOIN sovereign' in sql)
    assert 'ST_IsValid(g.geometry)' in sql
    assert 'NOT ST_IsEmpty(g.geometry)' in sql
    assert 'ST_SRID(g.geometry)' in sql
    assert 'ST_GeometryType(g.geometry)' in sql
    assert 'ST_CoveredBy(g.geometry,s.geometry)' in sql
    assert 'FROM geom g CROSS JOIN sovereign s' in sql
    assert 'ST_IsValid(geometry)' not in sql


def test_postgis_partition_sql_avoids_reserved_overlaps_cte_name():
    closure=build_city_closure('NG-PLC-000001')
    connection=_Connection();engine=PostGISSpatialTopologyEngine(connection,repair_mode=RepairMode.DISABLED)
    engine.assess(closure)
    partition_sql=[sql for sql,_ in connection.calls if 'ST_Intersection(a.geometry,b.geometry)' in sql]
    assert partition_sql
    for sql in partition_sql:
        assert re.search(r'(?m)^\s*overlaps\s+AS\s*\(',sql,re.IGNORECASE) is None
        assert 'peer_overlaps AS (' in sql
        assert 'FROM overlaps WHERE' not in sql
        assert 'FROM peer_overlaps WHERE' in sql
