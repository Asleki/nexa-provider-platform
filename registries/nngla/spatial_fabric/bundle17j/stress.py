from __future__ import annotations
from concurrent.futures import ThreadPoolExecutor
from time import perf_counter
from registries.nngla.spatial_fabric.bundle17g import CadastralSeriesDefinition, ParcelCandidateRecord, ParcelLifecycleStage, MemoryParcelReferenceAllocator
from registries.nngla.spatial_fabric.bundle17h import AddressSeriesDefinition, MemoryAddressAllocator, form_site_candidate
from registries.nngla.spatial_fabric.bundle17i import MemoryTitleReferenceAllocator, load_title_series
from .contracts import AllocatorFamily,ExecutionBasis,StressResult

def _result(sid,fam,n,ids,start):
    elapsed=(perf_counter()-start)*1000; unique=len(set(ids)); return StressResult(sid,fam,ExecutionBasis.MEMORY_CONTRACT,n,n,len(ids),unique,len(ids)-unique,0,0,0,0,0,elapsed,(len(ids)/(elapsed/1000)) if elapsed else 0,'PASS' if len(ids)==n and unique==n else 'FAIL')
def run_address_stress(n:int)->StressResult:
    series=AddressSeriesDefinition('addrseries:nngla:17j','NG-RD-000001','roadseg:nngla:17j','SEQUENTIAL','ROAD_SEGMENT','roadseg:nngla:17j',1,1,'INTEGER','NONE',False)
    a=MemoryAddressAllocator(); start=perf_counter()
    def one(i):
        s=form_site_candidate(road_id='NG-RD-000001',road_segment_id='roadseg:nngla:17j',source_reference=f'17j:addr:{i}')
        return a.reserve_next(series,site_id=s.site_id,idempotency_key=f'17j:addr:{i}')
    with ThreadPoolExecutor(max_workers=min(48,max(1,n))) as p: rows=tuple(p.map(one,range(n)))
    return _result(f'address-{n}',AllocatorFamily.ADDRESS_ID,n,[r.reserved_address_id for r in rows],start)

def run_address_display_stress(n:int)->StressResult:
    series=AddressSeriesDefinition('addrseries:nngla:17j-display','NG-RD-000001','roadseg:nngla:17j-display','SEQUENTIAL','ROAD_SEGMENT','roadseg:nngla:17j-display',1,1,'INTEGER','NONE',False)
    a=MemoryAddressAllocator(); start=perf_counter()
    def one(i):
        s=form_site_candidate(road_id='NG-RD-000001',road_segment_id='roadseg:nngla:17j-display',source_reference=f'17j:display:{i}')
        return a.reserve_next(series,site_id=s.site_id,idempotency_key=f'17j:display:{i}')
    with ThreadPoolExecutor(max_workers=min(48,max(1,n))) as p: rows=tuple(p.map(one,range(n)))
    return _result(f'address-display-{n}',AllocatorFamily.ADDRESS_DISPLAY_NUMBER,n,[f'{r.series_id}|{r.normalized_number_key}' for r in rows],start)

def run_parcel_stress(n:int)->StressResult:
    a=MemoryParcelReferenceAllocator(); series=CadastralSeriesDefinition('01','001'); start=perf_counter()
    def one(i):
        c=ParcelCandidateRecord(f'parcelcand:nngla:{i:064x}','ground:nngla:17j','UNCLASSIFIED','', 'PENDING',ParcelLifecycleStage.PARCEL_CANDIDATE,'production','RUNTIME_SCOPED',f'17j:parcel:{i}')
        return a.reserve(c,series)
    with ThreadPoolExecutor(max_workers=min(48,max(1,n))) as p: rows=tuple(p.map(one,range(n)))
    return _result(f'parcel-{n}',AllocatorFamily.PARCEL_REFERENCE,n,[r.parcel_id for r in rows],start)
def run_site_stress(n:int)->StressResult:
    start=perf_counter()
    def one(i): return form_site_candidate(road_id='NG-RD-000001',road_segment_id='roadseg:nngla:17j',source_reference=f'17j:site:{i}').site_id
    with ThreadPoolExecutor(max_workers=min(48,max(1,n))) as p: ids=tuple(p.map(one,range(n)))
    return _result(f'site-{n}',AllocatorFamily.SITE_ID,n,ids,start)
def run_title_stress(n:int)->StressResult:
    a=MemoryTitleReferenceAllocator(); series=load_title_series(); start=perf_counter()
    def one(i): return a.reserve(series,idempotency_key=f'17j:title:{i}').reserved_title_id
    with ThreadPoolExecutor(max_workers=min(48,max(1,n))) as p: ids=tuple(p.map(one,range(n)))
    return _result(f'title-{n}',AllocatorFamily.TITLE_REFERENCE,n,ids,start)
def run_memory_stress_matrix(levels=(1,10,100,1000)):
    out=[]
    for n in levels: out.extend((run_address_stress(n),run_address_display_stress(n),run_parcel_stress(n),run_site_stress(n),run_title_stress(n)))
    return tuple(out)
__all__=['run_address_stress','run_address_display_stress','run_parcel_stress','run_site_stress','run_title_stress','run_memory_stress_matrix']
