"""Bundle 19B materialization verification over committed governed artifacts."""
from __future__ import annotations
from ._shared import SUMMARY,json_payload
from .qualification import qualification_findings
def materialization_summary():
    findings=qualification_findings()
    if findings: raise RuntimeError('cannot materialize unqualified Bundle 19B: '+','.join(findings))
    summary=json_payload(SUMMARY)
    if summary.get('administrative_identity_count')!=192 or summary.get('qualified_count')!=192 or summary.get('legalization_approved_count')!=192: raise ValueError('Bundle 19B summary count mismatch')
    return summary
