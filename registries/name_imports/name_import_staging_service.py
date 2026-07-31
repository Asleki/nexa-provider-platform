from __future__ import annotations
from collections.abc import Callable
from datetime import datetime
from registries.adapters.csv.name_csv_row import NameCsvRow
from registries.names.name_kind import NameKind
from registries.names.name_sex_usage import NameSexUsage
from .name_candidate import NameCandidate
from .name_candidate_status import NameCandidateStatus
from .name_candidate_validator import NameCandidateValidator
class NameImportStagingService:
    def __init__(self,*,candidate_id_factory:Callable[[],str],clock:Callable[[],datetime],validator:NameCandidateValidator|None=None)->None:
        if not callable(candidate_id_factory) or not callable(clock): raise TypeError("candidate_id_factory and clock must be callable.")
        self._ids=candidate_id_factory; self._clock=clock; self._validator=validator or NameCandidateValidator()
    @staticmethod
    def _refs(value:str)->tuple[str,...]: return tuple(x.strip() for x in value.split("|") if x.strip())
    def stage(self,row:NameCsvRow,*,batch_id:str,source_id:str,runtime_mode:str)->NameCandidate:
        if not isinstance(row,NameCsvRow): raise TypeError("row must be NameCsvRow.")
        row_runtime=row.get("runtime_mode")
        attrs={}
        candidate=NameCandidate(candidate_id=self._ids(),batch_id=batch_id,source_id=source_id,source_row_number=row.row_number,raw_name_value=row.get("name"),name_kind=NameKind.parse(row.get("name_kind")),runtime_mode=runtime_mode,sex_usage=NameSexUsage.parse(row.get("sex_usage") or "unspecified"),source_reference=row.get("source_reference") or None,external_record_id=row.get("external_record_id") or None,language_refs=self._refs(row.get("language_refs")),country_refs=self._refs(row.get("country_refs")),region_refs=self._refs(row.get("region_refs")),culture_refs=self._refs(row.get("culture_refs")),script_code=row.get("script_code") or None,attributes=attrs,created_at=self._clock())
        validation=self._validator.validate(candidate,batch_runtime_mode=runtime_mode if not row_runtime else row_runtime)
        if validation.result.errors: status=NameCandidateStatus.REJECTED
        elif validation.result.warnings: status=NameCandidateStatus.QUARANTINED
        else: status=NameCandidateStatus.VALIDATED
        return candidate.with_status(status)
__all__=["NameImportStagingService"]
