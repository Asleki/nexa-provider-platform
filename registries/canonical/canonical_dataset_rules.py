"""Cross-contract validation rules for canonical dataset definitions."""
from __future__ import annotations
from dataclasses import dataclass
from .canonical_dataset_definition import CanonicalDatasetDefinition

@dataclass(frozen=True, slots=True)
class CanonicalDatasetFinding:
    code: str
    message: str

@dataclass(frozen=True, slots=True)
class CanonicalDatasetValidationResult:
    findings: tuple[CanonicalDatasetFinding, ...] = ()
    @property
    def is_valid(self) -> bool:
        return not self.findings
    def to_dict(self) -> dict[str, object]:
        return {"is_valid": self.is_valid, "findings": [{"code": f.code, "message": f.message} for f in self.findings]}

class CanonicalDatasetRules:
    """Pure rules that do not persist, approve, resolve or mutate datasets."""
    @staticmethod
    def validate(definition: CanonicalDatasetDefinition) -> CanonicalDatasetValidationResult:
        if not isinstance(definition, CanonicalDatasetDefinition):
            raise TypeError("definition must be a CanonicalDatasetDefinition.")
        findings: list[CanonicalDatasetFinding] = []
        for source in definition.source_datasets:
            if source.runtime_mode != definition.runtime_mode:
                findings.append(CanonicalDatasetFinding("CANONICAL_DATASET_RUNTIME_MISMATCH", "source dataset runtime_mode must match the derived dataset runtime_mode."))
        source_ids = {source.dataset_id for source in definition.source_datasets}
        if definition.dataset_id in source_ids:
            findings.append(CanonicalDatasetFinding("CANONICAL_DATASET_LINEAGE_CYCLE_RISK", "a dataset cannot derive from another version of itself in its immediate lineage."))
        return CanonicalDatasetValidationResult(tuple(findings))

__all__ = ["CanonicalDatasetFinding", "CanonicalDatasetValidationResult", "CanonicalDatasetRules"]
