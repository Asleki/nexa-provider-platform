from .contracts import QualificationDecision,QualificationReceipt
from infrastructure.governance.validation import ValidationOutcome
class QualificationService:
    def qualify(self,request,validation_receipt):
        if request.validation_receipt_id!=validation_receipt.validation_receipt_id: raise ValueError("validation receipt identity mismatch")
        decision={ValidationOutcome.passed:QualificationDecision.qualified,ValidationOutcome.failed:QualificationDecision.rejected,ValidationOutcome.quarantined:QualificationDecision.quarantined}[validation_receipt.outcome]
        return QualificationReceipt(request.qualification_id,request.validation_receipt_id,decision,f"validation outcome: {validation_receipt.outcome.value}")
