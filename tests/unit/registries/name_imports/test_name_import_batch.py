from datetime import datetime,timezone
import pytest
from registries.name_imports.name_candidate import NameCandidate
from registries.name_imports.name_import_batch import NameImportBatch
from registries.name_imports.name_candidate_status import NameCandidateStatus

def c(cid="candidate:1",status="validated",runtime="simulation"):
    return NameCandidate(cid,"batch:1","source:1",2,"Alex","first_name",runtime,status=status,created_at=datetime(2026,1,1,tzinfo=timezone.utc))
def test_batch_approval_marks_candidates_approved():
    approved=NameImportBatch("batch:1","simulation","source:1","names.csv",(c(),)).approve()
    assert approved.approved and approved.candidates[0].status is NameCandidateStatus.APPROVED

def test_batch_rejects_runtime_mismatch_duplicate_ids_and_unvalidated_approval():
    with pytest.raises(ValueError): NameImportBatch("batch:1","simulation","source:1","x",(c(runtime="production"),))
    with pytest.raises(ValueError): NameImportBatch("batch:1","simulation","source:1","x",(c(),c())).approve()
    with pytest.raises(ValueError): NameImportBatch("batch:1","simulation","source:1","x",(c(status="quarantined"),)).approve()
