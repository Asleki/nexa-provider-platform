from datetime import datetime,timezone
import pytest
from registries.names import CanonicalName,NameKind,NameMetadata
from registries.name_authority.generation import *
from registries.name_authority.authority import *
from registries.name_authority.repositories import MemoryNameAuthorityRepository

def n(i,v,k,attrs=None): return CanonicalName(i,v,k,NameMetadata(runtime_mode="simulation",attributes=attrs or {}))
def snapshot():
    names=[n("f1","Ava",NameKind.FIRST_NAME,{"seed":{"source_family":"novegeo"}}),n("f2","Noah",NameKind.FIRST_NAME),n("m1","Mae",NameKind.MIDDLE_NAME),n("m2","Kai",NameKind.MIDDLE_NAME),n("s1","Dube",NameKind.SURNAME),n("s2","Moyo",NameKind.SURNAME)]
    return GenerationSourceSnapshot.create("snapshot:1",names)
def request(count=4,batch=2): return SimulationGenerationRequest("batch:1","snapshot:1",snapshot().checksum,(GenerationFamilyTarget("novegeo_native_three_part",count),),"seed-1",batch)

def test_snapshot_is_stable_and_rejects_production():
    s=snapshot(); assert s.checksum==GenerationSourceSnapshot.create("snapshot:1",reversed(s.members)).checksum
    with pytest.raises(ValueError): AtomicNameGenerationProfile("x","X",NameKind.FIRST_NAME,"production")

def test_capacity_and_deterministic_generation():
    s=snapshot(); r=request(); cap=GenerationCapacityService().calculate(s,r)[0]
    assert cap.raw_capacity==8 and cap.is_sufficient
    g=SimulationNameGenerator(); a=g.generate(s,r,0,4); b=g.generate(s,r,0,4)
    assert [x[2].composition_key for x in a]==[x[2].composition_key for x in b]
    assert all(x[2].runtime_mode=="simulation" for x in a)

def test_batch_lifecycle_and_checkpointed_processing():
    s=snapshot(); r=request(); batch=GenerationBatch("batch:1",r).transition("validated").transition("ready")
    repo=MemoryGenerationRepository(); repo.add_snapshot(s); repo.add_batch(batch)
    authority=MemoryNameAuthorityRepository(); writer=MemoryBulkNameAuthorityWriter(authority); processor=GenerationBatchProcessor(SimulationNameGenerator(),repo,writer)
    batch=processor.run_next(batch,s); assert batch.status is GenerationBatchStatus.RUNNING and batch.next_sequence==2
    batch=processor.run_next(batch,s); assert batch.status is GenerationBatchStatus.COMPLETED and batch.inserted_count==4 and len(repo.commits)==2

def test_resume_rejects_changed_source_and_request():
    s=snapshot(); r=request(); b=GenerationBatch("batch:1",r).transition("validated").transition("ready")
    assert GenerationResumeValidator().validate(b,r,s)
    with pytest.raises(ValueError): GenerationResumeValidator().validate(b,request(batch=3),s)
