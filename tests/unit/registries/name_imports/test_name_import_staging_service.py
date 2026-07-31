from datetime import datetime,timezone
import itertools
from registries.adapters.csv.name_csv_row import NameCsvRow
from registries.name_imports.name_candidate_status import NameCandidateStatus
from registries.name_imports.name_import_staging_service import NameImportStagingService

def service():
    ids=iter(["candidate:1","candidate:2","candidate:3"])
    return NameImportStagingService(candidate_id_factory=lambda:next(ids),clock=lambda:datetime(2026,1,1,tzinfo=timezone.utc))

def test_stages_valid_row_without_writing_canonical_repository():
    row=NameCsvRow(2,{"name":"Alex","name_kind":"first_name","source_reference":"dataset:1","sex_usage":"unisex"})
    c=service().stage(row,batch_id="batch:1",source_id="source:1",runtime_mode="simulation")
    assert c.status is NameCandidateStatus.VALIDATED and c.runtime_mode=="simulation"

def test_quarantines_warning_and_rejects_runtime_mismatch():
    warning=service().stage(NameCsvRow(2,{"name":"Alex","name_kind":"first_name"}),batch_id="batch:1",source_id="source:1",runtime_mode="simulation")
    mismatch=service().stage(NameCsvRow(3,{"name":"Alex","name_kind":"first_name","source_reference":"dataset:1","runtime_mode":"production"}),batch_id="batch:1",source_id="source:1",runtime_mode="simulation")
    assert warning.status is NameCandidateStatus.QUARANTINED
    assert mismatch.status is NameCandidateStatus.REJECTED
