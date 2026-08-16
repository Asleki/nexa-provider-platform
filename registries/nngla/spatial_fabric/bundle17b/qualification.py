"""Bundle 17B aggregate qualification facade."""
from __future__ import annotations

from functools import lru_cache
from dataclasses import dataclass

from .containment import containment_findings, derive_containment_qualifications
from .crs_reconciliation import qualify_crs_occurrences
from .environment_binding import derive_environment_bindings, environment_binding_findings, environment_coverage_rows
from .precision import derive_precision_qualifications, precision_findings
from .source_fidelity import derive_source_fidelity_results, source_fidelity_findings


@dataclass(frozen=True, slots=True)
class Bundle17BQualification:
    crs_crosswalk_finding_count: int
    precision_record_count: int
    precision_finding_count: int
    containment_record_count: int
    containment_finding_count: int
    source_fidelity_record_count: int
    source_fidelity_finding_count: int
    environment_binding_count: int
    environment_finding_count: int
    environment_coverage_count: int
    qualification_status: str


@lru_cache(maxsize=1)
def qualify_bundle17b() -> Bundle17BQualification:
    crs_findings = qualify_crs_occurrences()
    precision = derive_precision_qualifications()
    precision_issues = precision_findings(precision)
    containment = derive_containment_qualifications()
    containment_issues = containment_findings(containment)
    fidelity = derive_source_fidelity_results()
    fidelity_issues = source_fidelity_findings(fidelity)
    bindings = derive_environment_bindings()
    environment_issues = environment_binding_findings(bindings)
    coverage = environment_coverage_rows(bindings)
    coverage_failed = tuple(row["spatial_reference_id"] for row in coverage if row["overall_coverage_status"] != "PASS")
    status = "PASS" if not (
        crs_findings or precision_issues or containment_issues or fidelity_issues or environment_issues or coverage_failed
    ) else "FAIL"
    return Bundle17BQualification(
        crs_crosswalk_finding_count=len(crs_findings),
        precision_record_count=len(precision),
        precision_finding_count=len(precision_issues),
        containment_record_count=len(containment),
        containment_finding_count=len(containment_issues),
        source_fidelity_record_count=len(fidelity),
        source_fidelity_finding_count=len(fidelity_issues),
        environment_binding_count=len(bindings),
        environment_finding_count=len(environment_issues),
        environment_coverage_count=len(coverage),
        qualification_status=status,
    )


def bundle17b_is_qualified() -> bool:
    return qualify_bundle17b().qualification_status == "PASS"


__all__ = ["Bundle17BQualification", "qualify_bundle17b", "bundle17b_is_qualified"]
