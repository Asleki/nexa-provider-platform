"""Sequential plan runner with explicit receipts."""
from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanStepReceipt:
    step_id:str; outcome:str; details:dict
class SequentialCataloguePlanRunner:
    def __init__(self,step_runner): self.step_runner=step_runner
    def run(self,plan,**kwargs):
        receipts=[]
        for step in plan.steps:
            result=self.step_runner(step,**kwargs); receipts.append(PlanStepReceipt(step.step_id,'passed',dict(result)))
        return tuple(receipts)
