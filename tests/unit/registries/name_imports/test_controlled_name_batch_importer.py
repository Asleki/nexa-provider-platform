from datetime import datetime,timezone
from registries.names.memory_name_repository import MemoryNameRepository
from registries.name_imports.name_candidate import NameCandidate
from registries.name_imports.name_import_batch import NameImportBatch
from registries.name_imports.controlled_name_batch_importer import ControlledNameBatchImporter
from registries.name_imports.name_import_results import NameImportOutcome

def candidate(cid,name,runtime="simulation"):
    return NameCandidate(cid,"batch:1","source:1",2,name,"first_name",runtime,source_reference="dataset:1",status="validated",created_at=datetime(2026,1,1,tzinfo=timezone.utc))
def importer(repo,ids):
    values=iter(ids)
    return ControlledNameBatchImporter(repo,name_id_factory=lambda:next(values),clock=lambda:datetime(2026,1,2,tzinfo=timezone.utc))
def test_imports_approved_batch_and_preserves_runtime_and_metadata():
    repo=MemoryNameRepository(); batch=NameImportBatch("batch:1","simulation","source:1","x",(candidate("candidate:1","Alex"),)).approve()
    result=importer(repo,["name:1"]).import_batch(batch)
    record=repo.get("name:1")
    assert result.imported_count==1 and result.complete
    assert record.metadata.runtime_mode=="simulation" and record.metadata.source_reference=="dataset:1"
def test_retry_returns_existing_without_duplicate():
    repo=MemoryNameRepository(); batch=NameImportBatch("batch:1","simulation","source:1","x",(candidate("candidate:1","Alex"),)).approve()
    importer(repo,["name:1"]).import_batch(batch)
    second=importer(repo,["name:2"]).import_batch(batch)
    assert second.items[0].outcome is NameImportOutcome.ALREADY_EXISTS
    assert second.items[0].canonical_name_id=="name:1" and repo.count()==1
def test_runtime_isolation_allows_same_text_in_different_modes():
    repo=MemoryNameRepository()
    sim=NameImportBatch("batch:1","simulation","source:1","x",(candidate("candidate:1","Alex"),)).approve()
    importer(repo,["name:sim"]).import_batch(sim)
    prodc=NameCandidate("candidate:2","batch:2","source:1",2,"Alex","first_name","production",source_reference="dataset:1",status="validated",created_at=datetime(2026,1,1,tzinfo=timezone.utc))
    prod=NameImportBatch("batch:2","production","source:1","x",(prodc,)).approve()
    importer(repo,["name:prod"]).import_batch(prod)
    assert repo.count()==2
def test_unapproved_batch_is_rejected():
    import pytest
    batch=NameImportBatch("batch:1","simulation","source:1","x",(candidate("candidate:1","Alex"),))
    with pytest.raises(ValueError): importer(MemoryNameRepository(),["name:1"]).import_batch(batch)
