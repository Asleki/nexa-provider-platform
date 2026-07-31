from __future__ import annotations
from registries.names.canonical_name import normalize_name_value
from registries.validators.validation_collector import RegistryValidationCollector
from registries.validators.validation_message import RegistryValidationMessage,ValidationSeverity
from .name_candidate import NameCandidate
from .name_candidate_validation import NameCandidateValidation
class NameCandidateValidator:
    def validate(self,candidate:NameCandidate,*,batch_runtime_mode:str|None=None)->NameCandidateValidation:
        if not isinstance(candidate,NameCandidate): raise TypeError("candidate must be NameCandidate.")
        c=RegistryValidationCollector()
        if not candidate.raw_name_value:
            c.add(RegistryValidationMessage(ValidationSeverity.ERROR,"NAME_IMPORT_EMPTY_NAME","raw_name_value","Name value cannot be empty.","Provide a name value."))
        else:
            try:
                normalized=normalize_name_value(candidate.raw_name_value)
                if normalized!=candidate.raw_name_value: c.add(RegistryValidationMessage(ValidationSeverity.WARNING,"NAME_IMPORT_NORMALIZED","raw_name_value","Name value changes during canonical normalization.",normalized))
            except (TypeError,ValueError) as exc: c.add(RegistryValidationMessage(ValidationSeverity.ERROR,"NAME_IMPORT_INVALID_NAME","raw_name_value",str(exc),None))
        if batch_runtime_mode is not None and candidate.runtime_mode!=batch_runtime_mode:
            c.add(RegistryValidationMessage(ValidationSeverity.ERROR,"NAME_IMPORT_RUNTIME_MISMATCH","runtime_mode","Candidate runtime mode does not match the batch.",None))
        if not candidate.source_reference: c.add(RegistryValidationMessage(ValidationSeverity.WARNING,"NAME_IMPORT_SOURCE_REFERENCE_MISSING","source_reference","Source reference is not supplied.","Provide a stable source reference when available."))
        return NameCandidateValidation(candidate,c.build(metadata={"candidate_id":candidate.candidate_id}))
__all__=["NameCandidateValidator"]
