from pathlib import Path
from .contracts import DeploymentQualification
from .inspector import DeploymentSourceInspector

class DeploymentQualificationService:
    def qualify(self, repository_root: Path) -> DeploymentQualification:
        findings = DeploymentSourceInspector(repository_root).inspect()
        return DeploymentQualification("I006", "PASSED" if all(f.passed for f in findings) else "FAILED", findings)
