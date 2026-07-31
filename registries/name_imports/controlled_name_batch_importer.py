from __future__ import annotations
from collections.abc import Callable
from datetime import datetime
from registries.names.canonical_name import CanonicalName
from registries.names.name_metadata import NameMetadata
from registries.names.name_repository import NameRepository
from registries.names.name_repository_errors import NameIdentityConflictError
from registries.names.name_search_query import NameSearchQuery
from registries.names.name_sex_usage_metadata import with_name_sex_usage
from .name_import_batch import NameImportBatch
from .name_candidate_status import NameCandidateStatus
from .name_import_results import NameImportBatchResult,NameImportItemResult,NameImportOutcome
class ControlledNameBatchImporter:
    def __init__(self,repository:NameRepository,*,name_id_factory:Callable[[],str],clock:Callable[[],datetime])->None:
        if not isinstance(repository,NameRepository): raise TypeError("repository must implement NameRepository.")
        if not callable(name_id_factory) or not callable(clock): raise TypeError("name_id_factory and clock must be callable.")
        self._repo=repository; self._ids=name_id_factory; self._clock=clock
    def _existing(self,candidate):
        result=self._repo.search(NameSearchQuery(text=candidate.raw_name_value,name_kind=candidate.name_kind,runtime_mode=candidate.runtime_mode,exact=True,limit=2))
        return result.records[0] if result.records else None
    def import_batch(self,batch:NameImportBatch)->NameImportBatchResult:
        if not isinstance(batch,NameImportBatch): raise TypeError("batch must be NameImportBatch.")
        if not batch.approved: raise ValueError("batch must be approved before import.")
        items=[]
        for candidate in batch.candidates:
            if candidate.status is not NameCandidateStatus.APPROVED:
                items.append(NameImportItemResult(candidate.candidate_id,NameImportOutcome.SKIPPED,message="candidate is not approved")); continue
            existing=self._existing(candidate)
            if existing is not None:
                items.append(NameImportItemResult(candidate.candidate_id,NameImportOutcome.ALREADY_EXISTS,existing.name_id)); continue
            try:
                metadata=NameMetadata(runtime_mode=candidate.runtime_mode,created_at=self._clock(),source_reference=candidate.source_reference,language_refs=candidate.language_refs,country_refs=candidate.country_refs,region_refs=candidate.region_refs,culture_refs=candidate.culture_refs,script_code=candidate.script_code,attributes=candidate.attributes)
                metadata=with_name_sex_usage(metadata,candidate.sex_usage)
                record=CanonicalName(self._ids(),candidate.raw_name_value,candidate.name_kind,metadata)
                self._repo.add(record)
                items.append(NameImportItemResult(candidate.candidate_id,NameImportOutcome.IMPORTED,record.name_id))
            except NameIdentityConflictError:
                existing=self._existing(candidate)
                items.append(NameImportItemResult(candidate.candidate_id,NameImportOutcome.ALREADY_EXISTS,existing.name_id if existing else None))
            except Exception as exc:
                items.append(NameImportItemResult(candidate.candidate_id,NameImportOutcome.FAILED,message=str(exc)))
        return NameImportBatchResult(batch.batch_id,tuple(items))
__all__=["ControlledNameBatchImporter"]
