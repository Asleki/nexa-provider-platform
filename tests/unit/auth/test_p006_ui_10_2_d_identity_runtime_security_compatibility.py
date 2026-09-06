from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import re

import pytest

from backend.auth.contracts import IdentityType, SelectedRuntime
from backend.auth.email_verification_persistence.contracts import EmailVerificationChallengeRecord


ROOT = Path(__file__).resolve().parents[3]
D_PACKAGE = ROOT / "backend/auth/email_verification_persistence"
D_MIGRATION = ROOT / "database/migrations/m006_10_02_email_verification_challenge.sql"
D_CLI = ROOT / "verification/auth/p006_ui_10_2_d_email_verification_challenge.py"
PWA_ENROLLMENT = ROOT / "frontend/src/ui/pages/developer-account-enrollment.js"


def test_d_preserves_exact_existing_identity_and_runtime_families() -> None:
    assert tuple(item.value for item in IdentityType) == ("guest", "nexadevs_developer")
    assert tuple(item.value for item in SelectedRuntime) == ("production", "simulation")
    sql = D_MIGRATION.read_text(encoding="utf-8").lower()
    assert "identity_type" not in sql
    assert "runtime_scope" not in sql
    assert "nexilabs_admin" not in sql
    assert "simulation_user" not in sql
    assert "production_user" not in sql


def test_d_persists_opaque_verifier_fields_without_raw_otp_column() -> None:
    names = {field.name for field in fields(EmailVerificationChallengeRecord)}
    assert "otp_verifier_scheme" in names
    assert "otp_verifier_version" in names
    assert "otp_verifier_payload" in names
    assert {"otp", "raw_otp", "otp_plaintext", "otp_code", "otp_value"}.isdisjoint(names)

    sql = D_MIGRATION.read_text(encoding="utf-8")
    create = re.search(
        r"CREATE TABLE nexilabs_auth\.email_verification_challenge\s*\((.*?)\n\);",
        sql,
        re.S,
    )
    assert create is not None
    table_sql = create.group(1).lower()
    for forbidden in ("raw_otp", "otp_plaintext", "otp_code ", "otp_value "):
        assert forbidden not in table_sql
    assert "otp_verifier_payload text not null" in table_sql
    assert "raw OTP and verifier key/pepper remain outside PostgreSQL" in sql


def test_d_package_has_no_mail_api_session_or_operational_otp_service() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(D_PACKAGE.glob("*.py"))
    )
    lower = combined.lower()
    for import_surface in ("fastapi", "mailgateway", "smtplib"):
        assert import_surface not in lower
    for method in ("def issue_otp", "def verify_otp", "def resend_otp", "def send_email"):
        assert method not in lower
    assert "mint sessions" in (D_PACKAGE / "postgresql.py").read_text(encoding="utf-8")


def test_d_cli_remains_qualification_only_and_password_is_prompted_not_flagged() -> None:
    text = D_CLI.read_text(encoding="utf-8")
    assert 'choices=("preflight", "verify", "adapter-proof")' in text
    assert 'getpass("PostgreSQL password: ")' in text
    assert "--password" not in text
    assert "migrationWritePerformed" in text
    assert "rawOtpPersisted" in text


def test_existing_pwa_otp_presentation_remains_foundation_only_when_full_repo_is_available() -> None:
    if not PWA_ENROLLMENT.is_file():
        pytest.skip("full frontend tree is not materialized in the assistant workspace")
    text = PWA_ENROLLMENT.read_text(encoding="utf-8")
    assert 'data-account-foundation-form="developer-email-verify"' in text
    assert 'data-account-foundation-only="true"' in text
    assert "No OTP is generated, sent or verified by this milestone." in text
    assert '<button class="secondary-button" type="button" disabled aria-disabled="true">Resend code</button>' in text
