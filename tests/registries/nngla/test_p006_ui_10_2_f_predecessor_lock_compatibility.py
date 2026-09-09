"""P006.UI.10.2.F — immutable E-prefix, additive F scope and no-roadmap/frontend lock."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest


E_TAG="P006.UI.10.2.E-credential-bundle-storage-delivery-persistence"
F_TAG="P006.UI.10.2.F-enrollment-notification-audit-persistence"
MANIFEST_PATH="database/migrations/migration_manifest.json"
F_MIGRATION_ID="m006_10_02_enrollment_notification_audit_persistence"
F_CORRECTION_MIGRATION_ID="m006_10_02_enrollment_notification_audit_filter_regex_correction"
ROADMAP_PATHS=(
    "ROADMAP.md","PWA_ROADMAP.md","ROADMAP_TRACKER.md","roadmap.py","roadmap_data.py",
    "roadmap_frontend.py","pwa_roadmap.py","pwa_roadmap_data.py","pwa_roadmap_frontend.py",
    "roadmap_tracker.py",
)
PROTECTED_FRONTEND_PREFIX="frontend/"
LOCKED_E_PRODUCTION_PATHS=(
    "backend/auth/credential_bundle_persistence/__init__.py",
    "backend/auth/credential_bundle_persistence/contracts.py",
    "backend/auth/credential_bundle_persistence/postgresql.py",
    "backend/auth/credential_bundle_persistence/qualification.py",
    "backend/auth/credential_bundle_persistence/service.py",
    "verification/auth/p006_ui_10_2_e_credential_bundle_storage_delivery.py",
    "database/migrations/m006_10_02_credential_bundle_storage_delivery.sql",
    "database/migrations/m006_10_02_credential_bundle_storage_delivery_rollback.sql",
)
ALLOWED_F_PATHS={
    "backend/auth/enrollment_notification_audit_persistence/__init__.py",
    "backend/auth/enrollment_notification_audit_persistence/contracts.py",
    "backend/auth/enrollment_notification_audit_persistence/postgresql.py",
    "backend/auth/enrollment_notification_audit_persistence/qualification.py",
    "backend/auth/enrollment_notification_audit_persistence/service.py",
    "database/migrations/m006_10_02_enrollment_notification_audit_persistence.sql",
    "database/migrations/m006_10_02_enrollment_notification_audit_persistence_rollback.sql",
    "database/migrations/m006_10_02_enrollment_notification_audit_filter_regex_correction.sql",
    "database/migrations/m006_10_02_enrollment_notification_audit_filter_regex_correction_rollback.sql",
    "tests/unit/database/migration_control/test_p006_ui_10_2_f_audit_filter_regex_correction_migration.py",
    MANIFEST_PATH,
    "verification/auth/p006_ui_10_2_f_enrollment_notification_audit_persistence.py",
    "tests/unit/auth/test_p006_ui_10_2_f_enrollment_notification_audit_contracts.py",
    "tests/unit/auth/test_p006_ui_10_2_f_enrollment_notification_audit_postgresql.py",
    "tests/unit/auth/test_p006_ui_10_2_f_enrollment_notification_audit_service.py",
    "tests/unit/auth/test_p006_ui_10_2_f_enrollment_notification_audit_cli.py",
    "tests/unit/auth/test_p006_ui_10_2_f_enrollment_notification_audit_qualification.py",
    "tests/unit/auth/test_p006_ui_10_2_f_enrollment_notification_audit_adapter_qualification.py",
    "tests/unit/auth/test_p006_ui_10_2_f_identity_runtime_security_compatibility.py",
    "tests/unit/database/migration_control/test_p006_ui_10_2_f_enrollment_notification_audit_persistence_migration.py",
    "tests/registries/nngla/test_p006_ui_10_2_f_predecessor_lock_compatibility.py",
}


def _root() -> Path:
    here=Path(__file__).resolve()
    for candidate in [here.parent,*here.parents]:
        if (candidate/'.git').exists() and (candidate/'database/migrations').is_dir():
            return candidate
    pytest.skip('git-backed repository required for predecessor lock proof')


def _git_bytes(root: Path, revision: str, path: str) -> bytes | None:
    proc=subprocess.run(['git','show',f'{revision}:{path}'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    return proc.stdout if proc.returncode==0 else None


def _tag_exists(root: Path, tag: str) -> bool:
    proc=subprocess.run(['git','rev-parse','-q','--verify',f'refs/tags/{tag}^{{}}'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    return proc.returncode==0


def _candidate_bytes(root: Path,path: str) -> bytes | None:
    if _tag_exists(root,F_TAG): return _git_bytes(root,F_TAG,path)
    candidate=root/path
    return candidate.read_bytes() if candidate.is_file() else None


def _candidate_changed_paths(root: Path) -> set[str]:
    if _tag_exists(root,F_TAG):
        proc=subprocess.run(['git','diff','--name-only',E_TAG,F_TAG,'--'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False)
        assert proc.returncode==0,proc.stderr
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    tracked=subprocess.run(['git','diff','--name-only',E_TAG,'--'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False)
    assert tracked.returncode==0,tracked.stderr
    untracked=subprocess.run(['git','ls-files','--others','--exclude-standard'],cwd=root,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,check=False)
    assert untracked.returncode==0,untracked.stderr
    return {line.strip() for text in (tracked.stdout,untracked.stdout) for line in text.splitlines() if line.strip()}


def test_f_manifest_is_exactly_two_governed_appends_after_e() -> None:
    root=_root(); e_raw=_git_bytes(root,E_TAG,MANIFEST_PATH); f_raw=_candidate_bytes(root,MANIFEST_PATH)
    assert e_raw is not None and f_raw is not None
    before=json.loads(e_raw.decode('utf-8')); candidate=json.loads(f_raw.decode('utf-8'))
    assert candidate['manifest_schema']==before['manifest_schema']
    assert candidate['manifest_schema_version']==before['manifest_schema_version']
    assert candidate['catalogue_version']==before['catalogue_version']+2
    assert len(candidate['migrations'])==len(before['migrations'])+2
    assert candidate['migrations'][:len(before['migrations'])]==before['migrations']
    row=candidate['migrations'][34]
    assert row['migration_id']==F_MIGRATION_ID and row['sequence_number']==35
    assert row['depends_on']==['m006_10_02_credential_bundle_storage_delivery']
    correction=candidate['migrations'][35]
    assert correction['migration_id']==F_CORRECTION_MIGRATION_ID
    assert correction['sequence_number']==36
    assert correction['depends_on']==[F_MIGRATION_ID]


def test_f_preserves_every_locked_e_production_file_byte_for_byte() -> None:
    root=_root()
    for path in LOCKED_E_PRODUCTION_PATHS:
        expected=_git_bytes(root,E_TAG,path); actual=_candidate_bytes(root,path)
        assert expected is not None and actual is not None,path
        assert actual==expected,f'F changed locked E production: {path}'


def test_f_candidate_scope_contains_only_the_approved_additive_surface() -> None:
    changed=_candidate_changed_paths(_root())
    assert changed<=ALLOWED_F_PATHS,f'unexpected F paths: {sorted(changed-ALLOWED_F_PATHS)}'
    assert MANIFEST_PATH in changed
    assert {
        'backend/auth/enrollment_notification_audit_persistence/contracts.py',
        'database/migrations/m006_10_02_enrollment_notification_audit_persistence.sql',
        'tests/unit/database/migration_control/test_p006_ui_10_2_f_enrollment_notification_audit_persistence_migration.py',
    }<=changed


def test_f_does_not_touch_any_roadmap_or_frontend_path() -> None:
    root=_root(); changed=_candidate_changed_paths(root)
    assert not any(path.startswith(PROTECTED_FRONTEND_PREFIX) for path in changed)
    assert not (set(ROADMAP_PATHS)&changed)
    for path in ROADMAP_PATHS:
        assert _candidate_bytes(root,path)==_git_bytes(root,E_TAG,path)
