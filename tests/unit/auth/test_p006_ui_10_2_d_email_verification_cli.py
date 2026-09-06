from __future__ import annotations

import json
from pathlib import Path

import pytest

from backend.auth.email_verification_persistence.contracts import (
    EmailVerificationAdapterQualificationReceipt,
    EmailVerificationQualificationReport,
)
from verification.auth import p006_ui_10_2_d_email_verification_challenge as cli


def _report(phase: str) -> EmailVerificationQualificationReport:
    return EmailVerificationQualificationReport(
        phase=phase,
        database_name="npp_dev",
        tls_active=True,
        repository_migration_count=33,
        database_migration_count=33,
        migration_tail_sequence=33,
        migration_tail_id="m006_10_02_email_verification_challenge",
        nexilabs_auth_tables=("email_verification_challenge",),
        public_schema_privilege_count=0,
        public_table_privilege_count=0,
        public_routine_privilege_count=0,
        principal_count=0,
        credential_count=0,
        developer_request_count=0,
        admin_operator_count=0,
        developer_decision_count=0,
        email_challenge_count=0,
        enigma_catalogue_count=3,
        enigma_catalogue_entry_count=279,
        enigma_profile_count=0,
        principal_enigma_profile_count=0,
    )


class Service:
    def preflight(self, *, expected_database): return _report("pre-D")
    def verify(self, *, expected_database): return _report("post-D")
    def qualify_adapter(self, *, expected_database):
        report = _report("post-D")
        receipt = EmailVerificationAdapterQualificationReceipt(
            "challenge:d", "principal:d", "email:d", "LOCKED",
            "keyed-hmac-sha256", True,
        )
        return report, receipt, report


class Pool:
    def __init__(self): self.closed = False
    def close(self): self.closed = True


def test_cli_verify_emits_only_safe_qualification_metadata(monkeypatch, capsys, tmp_path: Path) -> None:
    pool = Pool()
    monkeypatch.setattr(cli, "_service", lambda root: (Service(), pool))
    assert cli.main(["verify", "--repository-root", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["milestone"] == "P006.UI.10.2.D"
    assert payload["operation"] == "verify"
    assert payload["migrationWritePerformed"] is False
    assert payload["otpIssued"] is False
    assert payload["rawOtpPersisted"] is False
    assert pool.closed is True


def test_cli_adapter_proof_reports_rollback_without_secret_material(monkeypatch, capsys, tmp_path: Path) -> None:
    pool = Pool()
    monkeypatch.setattr(cli, "_service", lambda root: (Service(), pool))
    assert cli.main(["adapter-proof", "--repository-root", str(tmp_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["syntheticAuthorityRolledBack"] is True
    assert payload["adapter"]["challengeState"] == "LOCKED"
    rendered = json.dumps(payload).lower()
    assert "otpverifierpayload" not in rendered
    assert "qualification-keyed-verifier" not in rendered
    assert pool.closed is True


@pytest.mark.parametrize("command", ["issue", "resend", "verify-otp", "send-mail"])
def test_cli_has_no_operational_otp_commands(command: str) -> None:
    with pytest.raises(SystemExit):
        cli.main([command])
