import hashlib,json
from uuid import uuid4
from .contracts import FindingSeverity,ValidationOutcome,ValidationReceipt
class ValidationEngine:
    def __init__(self,rules): self.rules=tuple(rules)
    def validate(self,candidates,context,receipt_id=None):
        candidates=tuple(candidates); findings=[]
        for rule in self.rules:
            if hasattr(rule,"evaluate_all"): findings.extend(rule.evaluate_all(candidates,context))
            else:
                for candidate in candidates: findings.extend(rule.evaluate(candidate,context))
        findings=tuple(sorted(findings,key=lambda f:(f.candidate_id or "",f.code,f.message)))
        severities={f.severity for f in findings}
        outcome=ValidationOutcome.quarantined if FindingSeverity.quarantine in severities else ValidationOutcome.failed if FindingSeverity.error in severities else ValidationOutcome.passed
        rid=receipt_id or f"validation:{uuid4().hex}"
        canonical=json.dumps({"id":rid,"rules":[context.rule_set_id,context.rule_set_version],"candidateCount":len(candidates),"outcome":outcome.value,"findings":[[f.code,f.severity.value,f.candidate_id] for f in findings]},sort_keys=True,separators=(",",":"))
        return ValidationReceipt(rid,context,outcome,findings,len(candidates),hashlib.sha256(canonical.encode()).hexdigest())
