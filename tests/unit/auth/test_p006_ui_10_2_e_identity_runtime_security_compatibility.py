from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import re

from backend.auth.contracts import IdentityType, SelectedRuntime
from backend.auth.credential_bundle_persistence.contracts import (
    CredentialBundleRecord,
    CredentialBundleSecretRecord,
    CredentialDeliveryRecord,
)


ROOT = Path(__file__).resolve().parents[3]
E_PACKAGE = ROOT / "backend/auth/credential_bundle_persistence"
E_MIGRATION = ROOT / "database/migrations/m006_10_02_credential_bundle_storage_delivery.sql"
E_CLI = ROOT / "verification/auth/p006_ui_10_2_e_credential_bundle_storage_delivery.py"


def test_e_preserves_exact_existing_identity_and_runtime_families_without_persisting_runtime() -> None:
    assert tuple(item.value for item in IdentityType) == ("guest", "nexadevs_developer")
    assert tuple(item.value for item in SelectedRuntime) == ("production", "simulation")
    names = set(CredentialBundleRecord.__dataclass_fields__) | set(CredentialDeliveryRecord.__dataclass_fields__)
    assert "runtime" not in names and "runtime_scope" not in names
    sql = E_MIGRATION.read_text(encoding="utf-8").lower()
    for forbidden in ("runtime_scope", "nexilabs_admin", "simulation_user", "production_user"):
        assert forbidden not in sql


def test_e_contracts_have_no_raw_token_plaintext_password_or_public_url_field() -> None:
    names = {
        field.name
        for record_type in (CredentialBundleRecord, CredentialBundleSecretRecord, CredentialDeliveryRecord)
        for field in fields(record_type)
    }
    for forbidden in (
        "raw_token", "delivery_token", "archive_password", "plaintext_archive_password",
        "public_url", "presigned_url", "s3_url", "zip_blob", "bundle_blob",
    ):
        assert forbidden not in names
    assert "token_verifier_payload" in names
    assert "encrypted_secret_reference" in names
    assert "object_key" in names


def test_e_sql_has_no_binary_bundle_column_or_url_authority_and_rejects_url_shaped_object_key() -> None:
    sql = E_MIGRATION.read_text(encoding="utf-8")
    upper = sql.upper()
    assert "BYTEA" not in upper
    create = re.search(r"CREATE TABLE nexilabs_auth\.credential_bundle\s*\((.*?)\n\);", sql, re.S)
    assert create is not None
    table_sql = create.group(1).lower()
    for forbidden in ("public_url", "presigned_url", "archive_password", "zip_blob", "bundle_blob"):
        assert forbidden not in table_sql
    assert "object_key !~ '^[a-zA-Z][a-zA-Z0-9+.-]*://'" in sql
    assert "logical_delivery_host_code ~ '^[A-Z][A-Z0-9_]{2,79}$'" in sql


def test_e_package_has_no_cloud_mail_api_token_generation_or_account_activation_engine() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in sorted(E_PACKAGE.glob("*.py")))
    lower = combined.lower()
    for import_surface in ("import boto3", "from boto3", "fastapi", "smtplib", "mailgateway"):
        assert import_surface not in lower
    for method in (
        "def generate_bundle", "def upload_bundle", "def encrypt_archive", "def decrypt_archive",
        "def mint_token", "def verify_token", "def send_email", "def activate_account",
    ):
        assert method not in lower


def test_e_cli_is_qualification_only_and_prompts_for_database_password() -> None:
    text = E_CLI.read_text(encoding="utf-8")
    assert 'choices=("preflight", "verify", "adapter-proof")' in text
    assert 'getpass("PostgreSQL password: ")' in text
    assert "--password" not in text
    assert "bundleGenerated" in text
    assert "rawDeliveryTokenPersisted" in text
    assert "publicCredentialUrlActivated" in text
