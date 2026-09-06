from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass

from backend.auth.admin_review_persistence import qualification as subject
from backend.auth.admin_review_persistence.contracts import AdminOperatorRecord, DeveloperAccessDecisionRecord
from backend.auth.persistence.contracts import CredentialVerifierRecord


class Tx:
    def __init__(self): self.rolled_back = False
    def __enter__(self): return self
    def __exit__(self, exc_type, exc, tb):
        self.rolled_back = exc_type is not None
        return False


class Cursor:
    def __init__(self): self.calls=[]; self._result=[(0,)]
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def execute(self, sql, params=None):
        text = " ".join(str(sql).split())
        self.calls.append((text, params))
        self._result = [(0,)] if text.startswith("SELECT COUNT(*)") else []
    def fetchone(self): return self._result[0]


class Connection:
    def __init__(self): self.cursor_obj=Cursor(); self.tx=Tx()
    def cursor(self): return self.cursor_obj
    def transaction(self): return self.tx


class Pool:
    def __init__(self): self.connection_obj=Connection(); self.read_only=[]
    @contextmanager
    def connection(self, read_only=False):
        self.read_only.append(read_only)
        yield self.connection_obj


class FakeAuthority:
    def __init__(self, pool): pass
    def active_admin_operator(self, principal_id):
        return AdminOperatorRecord("admin-operator:qualification:p006-ui-10-2-c", principal_id, "QUALIFICATION-C-ADMIN-DEVELOPER-ID", "email:qualification:p006-ui-10-2-c", "qualification-c-admin@example.invalid", "ACTIVE", "now", None, None, "audit")
    def active_admin_operator_by_developer_id(self, value):
        return self.active_admin_operator("principal:qualification:p006-ui-10-2-c")
    def active_admin_password_verifier(self, principal_id):
        return CredentialVerifierRecord("credential:admin", principal_id, "ADMIN_PASSWORD", "qualification", 1, "opaque-qualification-verifier")
    def developer_access_decision(self, request_id):
        return DeveloperAccessDecisionRecord("developer-decision:qualification:p006-ui-10-2-c", request_id, "principal:qualification:p006-ui-10-2-c", "admin-operator:qualification:p006-ui-10-2-c", "APPROVED", None, None, "internal", "qualification-policy-v1", "receipt:qualification:p006-ui-10-2-c", "now")


def test_adapter_proof_uses_two_separate_password_kinds_and_rolls_back(monkeypatch) -> None:
    monkeypatch.setattr(subject, "PostgreSQLAdminReviewAuthority", FakeAuthority)
    pool = Pool()
    receipt = subject.PostgreSQLAdminReviewQualification(pool).qualify_adapter()
    assert receipt.rollback_verified is True
    assert pool.connection_obj.tx.rolled_back is True
    sql = "\n".join(statement for statement, _ in pool.connection_obj.cursor_obj.calls)
    assert "'password'" in sql
    assert "'ADMIN_PASSWORD'" in sql
    assert "INSERT INTO nexilabs_auth.admin_operator" in sql
    assert "INSERT INTO nexilabs_auth.developer_access_decision" in sql
    assert "SET CONSTRAINTS ALL IMMEDIATE" in sql
    assert sql.count("SELECT COUNT(*)") == 3
