from .contracts import FindingSeverity,ValidationFinding
class RequiredFieldsRule:
    def __init__(self,*fields): self.fields=tuple(fields)
    def evaluate(self,candidate,context):
        return tuple(ValidationFinding("REQUIRED_FIELD_MISSING",FindingSeverity.error,f"required field is missing: {f}",candidate.candidate_id,{"field":f}) for f in self.fields if candidate.payload.get(f) in {None,""})
class NamespacedIdentifierRule:
    def __init__(self,field): self.field=field
    def evaluate(self,candidate,context):
        value=candidate.payload.get(self.field)
        return () if isinstance(value,str) and ":" in value else (ValidationFinding("IDENTIFIER_NOT_NAMESPACED",FindingSeverity.error,f"{self.field} must be namespaced",candidate.candidate_id,{"field":self.field}),)
class AllowedValueRule:
    def __init__(self,field,allowed): self.field=field; self.allowed=frozenset(allowed)
    def evaluate(self,candidate,context):
        return () if candidate.payload.get(self.field) in self.allowed else (ValidationFinding("VALUE_NOT_ALLOWED",FindingSeverity.error,f"{self.field} has an unsupported value",candidate.candidate_id,{"field":self.field}),)
class DuplicateCandidateRule:
    def evaluate_all(self,candidates,context):
        seen=set(); findings=[]
        for c in candidates:
            key=repr(sorted(c.payload.items()))
            if key in seen: findings.append(ValidationFinding("DUPLICATE_CANDIDATE",FindingSeverity.quarantine,"duplicate candidate payload",c.candidate_id))
            seen.add(key)
        return tuple(findings)
