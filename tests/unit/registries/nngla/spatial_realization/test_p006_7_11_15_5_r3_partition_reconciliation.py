from pathlib import Path
import pytest

from registries.nngla.spatial_realization.closure import build_city_closure
from registries.nngla.spatial_realization.partition_reconciliation import (
    PartitionReconciliationError,
    reconcile_city_partition,
)
from registries.nngla.spatial_realization.topology import PostGISSpatialTopologyEngine


class Cursor:
    def __init__(self,conn):self.conn=conn;self.sql=''
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def execute(self,sql,params=()):
        assert sql.count('%s')==len(params)
        self.sql=sql;self.conn.calls.append(sql)
    def fetchall(self):
        ids=['__CITY__','NG-ADM-000013','NG-ADM-000014','NG-ADM-000015','NG-ADM-000016','NG-ADM-000017','NG-ADM-000018','NG-ADM-000019','NG-ADM-000020']
        return [(value,'00','POLYGON',8,self.conn.mapped,self.conn.ambiguous,0.001) for value in ids]


class Connection:
    def __init__(self,mapped=8,ambiguous=0):self.calls=[];self.mapped=mapped;self.ambiguous=ambiguous
    def cursor(self):return Cursor(self)


def test_r3_partition_is_one_shared_seeded_fabric_not_sequential_id_ownership():
    text=Path('registries/nngla/spatial_realization/partition_reconciliation.py').read_text()
    for token in ('ST_VoronoiPolygons','defect AS','positive_overlaps AS','stable AS','final_children AS','ST_Covers'):
        assert token in text
    assert 'rsplit' not in text
    assert 'ST_SnapToGrid' not in text
    assert 'R3_FINAL_PARTITION' in text


def test_r3_partition_returns_city_and_all_eight_successor_children_from_same_statement():
    closure=build_city_closure('NG-PLC-000001')
    engine=PostGISSpatialTopologyEngine(Connection())
    result=reconcile_city_partition(
        engine.connection,
        closure,
        closure.admin_root,
        closure.exhaustive_children,
        engine._successor,
    )
    assert result.city.is_source_successor
    assert len(result.children)==8
    assert all(item.is_source_successor for item in result.children)
    assert len(engine.connection.calls)==1


def test_ambiguous_canonical_seed_cell_mapping_fails_closed():
    closure=build_city_closure('NG-PLC-000001')
    engine=PostGISSpatialTopologyEngine(Connection(mapped=7,ambiguous=1))
    with pytest.raises(PartitionReconciliationError,match='ambiguous'):
        reconcile_city_partition(engine.connection,closure,closure.admin_root,closure.exhaustive_children,engine._successor)
