import pytest
from infrastructure.deployment.contracts.receipts import DeploymentReceipt, RollbackReceipt

def test_deployment_receipt_preserves_release_and_no_database_writes():
    receipt=DeploymentReceipt("deploy:1","release:abc1234","abc1234","development","passed","https://api.example/health","2026-08-05T00:00:00Z")
    assert receipt.to_dict()["database_writes_performed"] == 0

def test_deployment_receipt_rejects_ambiguous_identity():
    with pytest.raises(ValueError):
        DeploymentReceipt("1","release:abc1234","abc1234","development","passed","https://api.example/health","now")

def test_rollback_is_separate_from_database_state():
    receipt=RollbackReceipt("rollback:1","release:new","release:old","passed","healthy","now")
    assert receipt.database_writes_performed == 0
