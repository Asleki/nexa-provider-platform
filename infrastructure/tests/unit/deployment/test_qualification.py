from pathlib import Path
from infrastructure.deployment.qualification.service import DeploymentQualificationService

def test_repository_deployment_assets_qualify():
    root=Path(__file__).resolve().parents[4]
    result=DeploymentQualificationService().qualify(root)
    assert result.status == "PASSED"
    assert result.database_writes_performed == 0
    assert all(item.passed for item in result.findings)
