from concurrent.futures import ThreadPoolExecutor
import pytest
from registries.nngla.spatial_fabric.bundle17k import MemoryGeometryIdAllocator

def test_first_safe_geometry_id_follows_bundle17e_namespace(): assert MemoryGeometryIdAllocator().reserve(idempotency_key='a')=='NG-GEO-002433'
def test_geometry_allocator_is_idempotent_and_parallel_unique():
 a=MemoryGeometryIdAllocator();
 def one(i): return a.reserve(idempotency_key=f'k:{i}')
 with ThreadPoolExecutor(max_workers=32) as p: ids=tuple(p.map(one,range(1000)))
 assert len(set(ids))==1000 and min(ids)=='NG-GEO-002433'
def test_simulation_cannot_consume_sovereign_geometry_ids():
 with pytest.raises(ValueError): MemoryGeometryIdAllocator().reserve(idempotency_key='sim',authority_runtime_mode='simulation')
