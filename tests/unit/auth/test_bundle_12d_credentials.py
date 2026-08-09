from pathlib import Path
import json

from backend.auth.contracts import IdentityType
from backend.auth.credentials import DevelopmentCredentialStore, hash_password, verify_password


def test_password_verifier_and_stable_principal_contract(tmp_path: Path) -> None:
    verifier = hash_password("correct-password", salt=b"0123456789abcdef", iterations=1000)
    assert verify_password("correct-password", verifier)
    assert not verify_password("wrong-password", verifier)

    credential_dir = tmp_path / "credentials"
    credential_dir.mkdir()
    (credential_dir / "guests.local.json").write_text(json.dumps([{
        "principalId": "guest:test:0001",
        "username": "guest",
        "identityType": "guest",
        "credentialVerifier": verifier,
        "enabled": True,
        "permissions": ["public:search"],
    }]))
    (credential_dir / "developers.local.json").write_text(json.dumps([{
        "principalId": "developer:test:0001",
        "username": "developer",
        "identityType": "nexadevs_developer",
        "credentialVerifier": verifier,
        "enabled": True,
        "permissions": ["registry:view"],
        "enigmaProfileId": "profile:test",
    }]))

    store = DevelopmentCredentialStore(credential_dir)
    principal = store.authenticate("guest", "correct-password", IdentityType.GUEST)
    assert principal is not None
    assert principal.principal_id == "guest:test:0001"
    assert principal.username == "guest"
