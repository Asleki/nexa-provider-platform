import json
from .contracts import DeploymentQualification

def format_human(result: DeploymentQualification) -> str:
    lines=["I006 DEPLOYMENT PACKAGE QUALIFICATION", "="*72, f"Status: {result.status}", f"Database writes performed: {result.database_writes_performed}", "", "FINDINGS"]
    lines.extend(f"- {'PASS' if f.passed else 'FAIL'} {f.code}: {f.message}" for f in result.findings)
    return "\n".join(lines)

def format_json(result: DeploymentQualification) -> str:
    return json.dumps(result.to_dict(), indent=2, sort_keys=True)
