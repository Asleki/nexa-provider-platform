from dataclasses import dataclass
from registries.validators.validation_result import RegistryValidationResult
from .name_candidate import NameCandidate
@dataclass(frozen=True,slots=True)
class NameCandidateValidation:
    candidate:NameCandidate; result:RegistryValidationResult
    def __post_init__(self):
        if not isinstance(self.candidate,NameCandidate): raise TypeError("candidate must be NameCandidate.")
        if not isinstance(self.result,RegistryValidationResult): raise TypeError("result must be RegistryValidationResult.")
__all__=["NameCandidateValidation"]
