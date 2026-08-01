from registries.names import CanonicalName,NameKind,NameMetadata
from registries.name_authority.generation import *
from registries.name_authority.authority import *
from registries.name_authority.repositories import MemoryNameAuthorityRepository
from registries.name_authority.read_models import *

def n(i,v,k): return CanonicalName(i,v,k,NameMetadata(runtime_mode="simulation"))
def test_bundle_c_zero_person_end_to_end_generation_resume_projection_search():
    names=[n("f1","Ava",NameKind.FIRST_NAME),n("f2","Noah",NameKind.FIRST_NAME),n("m1","Mae",NameKind.MIDDLE_NAME),n("m2","Kai",NameKind.MIDDLE_NAME),n("s1","Dube",NameKind.SURNAME),n("s2","Moyo",NameKind.SURNAME)]
    snap=GenerationSourceSnapshot.create("snapshot:founding",names)
    req=SimulationGenerationRequest("batch:founding","snapshot:founding",snap.checksum,(GenerationFamilyTarget("novegeo_native_three_part",6),),"founding-seed",2)
    batch=GenerationBatch(req.generation_batch_id,req).transition("validated").transition("ready")
    gen_repo=MemoryGenerationRepository(); gen_repo.add_snapshot(snap); gen_repo.add_batch(batch)
    authority_repo=MemoryNameAuthorityRepository(); processor=GenerationBatchProcessor(SimulationNameGenerator(),gen_repo,MemoryBulkNameAuthorityWriter(authority_repo))
    while batch.status is not GenerationBatchStatus.COMPLETED: batch=processor.run_next(batch,snap)
    assert batch.next_sequence==6 and batch.failed_count==0
    read_repo=MemoryNameAuthorityReadRepository(); records=list(authority_repo._d.values()); cp=NameAuthorityReadModelProjector().rebuild(records,read_repo,"simulation")
    assert cp.projected_count==6 and read_repo.statistics("simulation").total==6
    result=read_repo.search(NameAuthoritySearchQuery("simulation",limit=3)); assert len(result.items)==3 and result.has_more
    assert all("person_id" not in dict(x.metadata) and "citizen_id" not in dict(x.metadata) for x in result.items)
