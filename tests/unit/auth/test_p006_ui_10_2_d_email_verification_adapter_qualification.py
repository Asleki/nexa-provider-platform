from __future__ import annotations

from contextlib import contextmanager

from backend.auth.email_verification_persistence import qualification as subject
from backend.auth.email_verification_persistence.contracts import EmailVerificationChallengeRecord


class Tx:
    def __init__(self): self.rolled_back = False
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        self.rolled_back = exc_type is not None
        return False


class Cursor:
    def __init__(self): self.calls = []; self._result = [(0,)]
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, params=None):
        text = " ".join(str(sql).split())
        self.calls.append((text, params))
        if text.startswith("SELECT COUNT(*)"):
            self._result = [(0,)]
        else:
            self._result = []
    def fetchone(self): return self._result[0]


class Connection:
    def __init__(self): self.cursor_obj = Cursor(); self.tx = Tx()
    def cursor(self): return self.cursor_obj
    def transaction(self): return self.tx


class Pool:
    def __init__(self): self.connection_obj = Connection(); self.read_only = []
    @contextmanager
    def connection(self, read_only=False):
        self.read_only.append(read_only)
        yield self.connection_obj


def _record(state: str, attempts: int) -> EmailVerificationChallengeRecord:
    return EmailVerificationChallengeRecord(
        challenge_id="email-challenge:qualification:p006-ui-10-2-d",
        principal_id="principal:qualification:p006-ui-10-2-d",
        email_id="email:qualification:p006-ui-10-2-d",
        otp_verifier_scheme="qualification-keyed-v1",
        otp_verifier_version=1,
        otp_verifier_payload="qualification-keyed-verifier-material-opaque",
        challenge_state=state,
        policy_version="qualification-policy-v1",
        issued_at="now",
        expires_at="later",
        consumed_at=None,
        invalidated_at=None,
        attempt_count=attempts,
        max_attempts=2,
        resend_count=0,
        last_resend_at=None,
    )


class FakeAuthority:
    def __init__(self, pool): pass
    def issued_challenge(self, *, principal_id, email_id):
        return _record("ISSUED", 0)
    def challenge_by_id(self, challenge_id):
        return _record("LOCKED", 2)


def test_adapter_proof_uses_opaque_verifier_exercises_lock_and_rolls_back(monkeypatch) -> None:
    monkeypatch.setattr(subject, "PostgreSQLEmailVerificationAuthority", FakeAuthority)
    pool = Pool()
    receipt = subject.PostgreSQLEmailVerificationQualification(pool).qualify_adapter()
    assert receipt.rollback_verified is True
    assert receipt.challenge_state == "LOCKED"
    assert receipt.verifier_scheme == "qualification-keyed-v1"
    assert pool.connection_obj.tx.rolled_back is True

    sql = "\n".join(statement for statement, _ in pool.connection_obj.cursor_obj.calls)
    assert "INSERT INTO nexilabs_auth.principal_account" in sql
    assert "INSERT INTO nexilabs_auth.account_email" in sql
    assert "INSERT INTO nexilabs_auth.email_verification_challenge" in sql
    assert "'qualification-keyed-v1'" in sql
    assert "SET attempt_count = max_attempts" in sql
    assert "challenge_state = 'LOCKED'" in sql
    assert sql.count("SELECT COUNT(*)") == 3
    assert "otp_plaintext" not in sql.lower()
    assert "raw_otp" not in sql.lower()
