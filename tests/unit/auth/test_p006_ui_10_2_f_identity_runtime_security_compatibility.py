from __future__ import annotations

from dataclasses import fields
from pathlib import Path
import re

from backend.auth.enrollment_notification_audit_persistence.contracts import (
    ADMIN_OPERATIONS_RECIPIENT_REFERENCE,
    AuditExportRecord,
    EnrollmentEventRecord,
    NotificationDeliveryRecord,
)


ROOT=Path(__file__).resolve().parents[3]
F_PACKAGE=ROOT/'backend/auth/enrollment_notification_audit_persistence'
F_MIGRATION=ROOT/'database/migrations/m006_10_02_enrollment_notification_audit_persistence.sql'
F_CLI=ROOT/'verification/auth/p006_ui_10_2_f_enrollment_notification_audit_persistence.py'


def test_f_does_not_create_a_third_identity_or_persist_runtime_selection() -> None:
    names={field.name for record in (EnrollmentEventRecord,NotificationDeliveryRecord,AuditExportRecord) for field in fields(record)}
    assert 'runtime' not in names and 'runtime_scope' not in names and 'identity_type' not in names
    sql=F_MIGRATION.read_text(encoding='utf-8').lower()
    for forbidden in ('create table nexilabs_auth.principal_account',"'nexilabs_admin'",'simulation_user','production_user','runtime_scope'):
        assert forbidden not in sql
    assert "identity_type" in sql  # only read to validate ACCOUNT_ACTIVATED against existing authority
    assert "principal_identity_value is distinct from 'nexadevs_developer'" in sql


def test_f_persistence_has_no_raw_mail_or_credential_material_fields() -> None:
    names={field.name for record in (EnrollmentEventRecord,NotificationDeliveryRecord,AuditExportRecord) for field in fields(record)}
    forbidden={
        'email_address','applicant_name','first_name','last_name','date_of_birth','message_body',
        'rendered_body','html_body','text_body','password','otp','otp_value','developer_setup_secret',
        'archive_password','enigma_response','raw_token','raw_download_token','provider_credential',
        'provider_api_key','public_url','presigned_url','artifact_bytes','report_bytes',
    }
    assert not (names & forbidden)
    assert ADMIN_OPERATIONS_RECIPIENT_REFERENCE=='NEXILABS_ADMIN_OPERATIONS'


def test_f_package_has_no_mail_cloud_report_generation_api_or_account_activation_engine() -> None:
    combined='\n'.join(path.read_text(encoding='utf-8') for path in sorted(F_PACKAGE.glob('*.py')))
    lower=combined.lower()
    for import_surface in ('import boto3','from boto3','smtplib','fastapi','mailgateway','sendgrid','mailgun'):
        assert import_surface not in lower
    for method in (
        'def send_mail','def render_mail','def retry_mail','def generate_export','def upload_export',
        'def presign','def activate_account','def create_event','def record_notification',
    ):
        assert method not in lower


def test_f_sql_reference_only_admin_alert_has_no_current_mailbox_identity() -> None:
    sql=F_MIGRATION.read_text(encoding='utf-8').lower()
    assert 'nexilabs_admin_operations'.lower() in sql
    assert 'nexatech.core@gmail.com' not in sql
    assert not re.search(r"[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}", sql)


def test_f_audit_artifact_contract_is_private_reference_not_blob_or_public_url() -> None:
    sql=F_MIGRATION.read_text(encoding='utf-8').lower()
    audit=re.search(r"create table nexilabs_auth\.audit_export\s*\((.*?)\n\);",sql,re.S)
    assert audit is not None
    table=audit.group(1)
    assert 'object_provider_code' in table and 'object_key' in table
    assert 'content_sha256' in table and 'byte_size' in table
    assert 'bytea' not in table and 'public_url' not in table and 'presigned_url' not in table
    assert "object_key !~ '^[a-za-z][a-za-z0-9+.-]*://'" in table


def test_f_cli_is_qualification_only_and_database_password_is_private_prompt() -> None:
    text=F_CLI.read_text(encoding='utf-8')
    assert 'choices=("preflight", "verify", "adapter-proof")' in text
    assert 'getpass("PostgreSQL password: ")' in text
    assert '--password' not in text
    assert 'mailSent' in text and 'auditArtifactGenerated' in text
    assert 'rawCredentialMaterialPersisted' in text and 'accountActivationOperationPerformed' in text
