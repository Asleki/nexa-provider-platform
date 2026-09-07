"""P006.UI.10.2.E — immutable D-prefix, exact scope and no-roadmap/frontend lock."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest


D_TAG = "P006.UI.10.2.D-email-verification-challenge-persistence"
E_TAG = "P006.UI.10.2.E-credential-bundle-storage-delivery-persistence"
MANIFEST_PATH = "database/migrations/migration_manifest.json"
E_MIGRATION_ID = "m006_10_02_credential_bundle_storage_delivery"
ROADMAP_PATHS = (
    "ROADMAP.md", "PWA_ROADMAP.md", "ROADMAP_TRACKER.md", "roadmap.py",
    "roadmap_data.py", "roadmap_frontend.py", "pwa_roadmap.py",
    "pwa_roadmap_data.py", "pwa_roadmap_frontend.py", "roadmap_tracker.py",
)
PROTECTED_FRONTEND_PREFIX = "frontend/"
LOCKED_D_PRODUCTION_PATHS = (
    "backend/auth/email_verification_persistence/__init__.py",
    "backend/auth/email_verification_persistence/contracts.py",
    "backend/auth/email_verification_persistence/postgresql.py",
    "backend/auth/email_verification_persistence/qualification.py",
    "backend/auth/email_verification_persistence/service.py",
    "verification/auth/p006_ui_10_2_d_email_verification_challenge.py",
    "database/migrations/m006_10_02_email_verification_challenge.sql",
    "database/migrations/m006_10_02_email_verification_challenge_rollback.sql",
)
APPROVED_D_COMPATIBILITY_PATHS = {
    "tests/registries/nngla/test_p006_ui_10_2_d_predecessor_lock_compatibility.py",
    "tests/unit/auth/test_p006_ui_10_2_d_email_verification_qualification.py",
}
ALLOWED_E_PATHS = {
    "backend/auth/credential_bundle_persistence/__init__.py",
    "backend/auth/credential_bundle_persistence/contracts.py",
    "backend/auth/credential_bundle_persistence/postgresql.py",
    "backend/auth/credential_bundle_persistence/qualification.py",
    "backend/auth/credential_bundle_persistence/service.py",
    "database/migrations/m006_10_02_credential_bundle_storage_delivery.sql",
    "database/migrations/m006_10_02_credential_bundle_storage_delivery_rollback.sql",
    "database/migrations/migration_manifest.json",
    "verification/auth/p006_ui_10_2_e_credential_bundle_storage_delivery.py",
    "tests/unit/auth/test_p006_ui_10_2_e_credential_bundle_adapter_qualification.py",
    "tests/unit/auth/test_p006_ui_10_2_e_credential_bundle_cli.py",
    "tests/unit/auth/test_p006_ui_10_2_e_credential_bundle_contracts.py",
    "tests/unit/auth/test_p006_ui_10_2_e_credential_bundle_postgresql.py",
    "tests/unit/auth/test_p006_ui_10_2_e_credential_bundle_qualification.py",
    "tests/unit/auth/test_p006_ui_10_2_e_credential_bundle_service.py",
    "tests/unit/auth/test_p006_ui_10_2_e_identity_runtime_security_compatibility.py",
    "tests/unit/database/migration_control/test_p006_ui_10_2_e_credential_bundle_storage_delivery_migration.py",
    "tests/registries/nngla/test_p006_ui_10_2_e_predecessor_lock_compatibility.py",
    *APPROVED_D_COMPATIBILITY_PATHS,
}


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "database/migrations").is_dir():
            return candidate
    pytest.skip("git-backed repository required for predecessor lock proof")


def _git_bytes(root: Path, revision: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", f"{revision}:{path}"], cwd=root,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def _tag_exists(root: Path, tag: str) -> bool:
    proc = subprocess.run(
        ["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}^{{}}"],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    return proc.returncode == 0


def _candidate_bytes(root: Path, path: str) -> bytes | None:
    if _tag_exists(root, E_TAG):
        return _git_bytes(root, E_TAG, path)
    candidate = root / path
    return candidate.read_bytes() if candidate.is_file() else None


def _candidate_changed_paths(root: Path) -> set[str]:
    if _tag_exists(root, E_TAG):
        proc = subprocess.run(
            ["git", "diff", "--name-only", D_TAG, E_TAG, "--"], cwd=root,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
        )
        assert proc.returncode == 0, proc.stderr
        return {line.strip() for line in proc.stdout.splitlines() if line.strip()}
    tracked = subprocess.run(
        ["git", "diff", "--name-only", D_TAG, "--"], cwd=root,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    assert tracked.returncode == 0, tracked.stderr
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=root,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    assert untracked.returncode == 0, untracked.stderr
    return {
        line.strip()
        for text in (tracked.stdout, untracked.stdout)
        for line in text.splitlines()
        if line.strip()
    }


def test_e_manifest_is_exactly_one_governed_append_after_d() -> None:
    root = _root()
    d_raw = _git_bytes(root, D_TAG, MANIFEST_PATH)
    e_raw = _candidate_bytes(root, MANIFEST_PATH)
    assert d_raw is not None and e_raw is not None
    before = json.loads(d_raw.decode("utf-8"))
    candidate = json.loads(e_raw.decode("utf-8"))
    assert candidate["manifest_schema"] == before["manifest_schema"]
    assert candidate["manifest_schema_version"] == before["manifest_schema_version"]
    assert candidate["catalogue_version"] == before["catalogue_version"] + 1
    assert len(candidate["migrations"]) == len(before["migrations"]) + 1
    assert candidate["migrations"][:len(before["migrations"])] == before["migrations"]
    assert candidate["migrations"][33]["migration_id"] == E_MIGRATION_ID
    assert candidate["migrations"][33]["sequence_number"] == 34


def test_e_preserves_every_locked_d_production_file_byte_for_byte() -> None:
    root = _root()
    for path in LOCKED_D_PRODUCTION_PATHS:
        expected = _git_bytes(root, D_TAG, path)
        actual = _candidate_bytes(root, path)
        assert expected is not None and actual is not None, path
        assert actual == expected, f"E changed locked D production: {path}"


def test_e_candidate_scope_contains_only_the_approved_additive_surface() -> None:
    changed = _candidate_changed_paths(_root())
    assert changed <= ALLOWED_E_PATHS, f"unexpected E paths: {sorted(changed - ALLOWED_E_PATHS)}"
    assert APPROVED_D_COMPATIBILITY_PATHS <= changed
    assert MANIFEST_PATH in changed


def test_e_does_not_touch_any_roadmap_or_frontend_path() -> None:
    root = _root()
    changed = _candidate_changed_paths(root)
    assert not any(path.startswith(PROTECTED_FRONTEND_PREFIX) for path in changed)
    assert not (set(ROADMAP_PATHS) & changed)
    for path in ROADMAP_PATHS:
        assert _candidate_bytes(root, path) == _git_bytes(root, D_TAG, path)
