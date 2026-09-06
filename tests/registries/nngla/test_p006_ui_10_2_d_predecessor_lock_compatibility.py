"""P006.UI.10.2.D — immutable C-prefix, compatibility-maintenance and no-roadmap lock."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest


C_TAG = "P006.UI.10.2.C-layered-admin-review-authority-persistence"
MANIFEST_PATH = "database/migrations/migration_manifest.json"
D_MIGRATION_ID = "m006_10_02_email_verification_challenge"
ROADMAP_PATHS = (
    "ROADMAP.md",
    "PWA_ROADMAP.md",
    "ROADMAP_TRACKER.md",
    "roadmap.py",
    "roadmap_data.py",
    "roadmap_frontend.py",
    "pwa_roadmap.py",
    "pwa_roadmap_data.py",
    "pwa_roadmap_frontend.py",
    "roadmap_tracker.py",
)
LOCKED_C_PRODUCTION_PATHS = (
    "backend/auth/admin_review_persistence/__init__.py",
    "backend/auth/admin_review_persistence/contracts.py",
    "backend/auth/admin_review_persistence/postgresql.py",
    "backend/auth/admin_review_persistence/qualification.py",
    "backend/auth/admin_review_persistence/service.py",
    "verification/auth/p006_ui_10_2_c_admin_review_authority.py",
    "database/migrations/m006_10_02_layered_admin_review_authority.sql",
    "database/migrations/m006_10_02_layered_admin_review_authority_rollback.sql",
)
APPROVED_C_COMPATIBILITY_PATHS = {
    "tests/unit/database/migration_control/test_p006_ui_10_2_c_admin_review_authority_migration.py",
    "tests/registries/nngla/test_p006_ui_10_2_c_predecessor_lock_compatibility.py",
}
C_OWNED_PREFIXES = (
    "backend/auth/admin_review_persistence/",
    "verification/auth/p006_ui_10_2_c_admin_review_authority.py",
    "tests/unit/auth/test_p006_ui_10_2_c_",
    "tests/unit/database/migration_control/test_p006_ui_10_2_c_",
    "tests/registries/nngla/test_p006_ui_10_2_c_",
)
PWA_OTP_PRESENTATION = "frontend/src/ui/pages/developer-account-enrollment.js"


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "database/migrations").is_dir():
            return candidate
    pytest.skip("git-backed repository required for predecessor lock proof")


def _git_bytes(root: Path, revision: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def _changed_tracked_paths(root: Path) -> set[str]:
    proc = subprocess.run(
        ["git", "diff", "--name-only", C_TAG, "--"],
        cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return {line.strip() for line in proc.stdout.splitlines() if line.strip()}


def test_d_manifest_is_exactly_one_governed_append_after_c() -> None:
    root = _root()
    c_raw = _git_bytes(root, C_TAG, MANIFEST_PATH)
    assert c_raw is not None, "C annotated tag manifest is unavailable"
    before = json.loads(c_raw.decode("utf-8"))
    current = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    assert current["manifest_schema"] == before["manifest_schema"]
    assert current["manifest_schema_version"] == before["manifest_schema_version"]
    assert current["catalogue_version"] == before["catalogue_version"] + 1
    assert len(current["migrations"]) == len(before["migrations"]) + 1
    assert current["migrations"][: len(before["migrations"])] == before["migrations"]
    assert current["migrations"][32]["migration_id"] == D_MIGRATION_ID
    assert current["migrations"][32]["sequence_number"] == 33


def test_d_preserves_locked_c_production_semantics_outside_approved_compatibility() -> None:
    root = _root()
    for path in LOCKED_C_PRODUCTION_PATHS:
        expected = _git_bytes(root, C_TAG, path)
        assert expected is not None, path
        assert (root / path).read_bytes() == expected, path


def test_d_changes_only_approved_c_owned_compatibility_paths() -> None:
    root = _root()
    changed = _changed_tracked_paths(root)
    changed_c_owned = {
        path for path in changed
        if any(path.startswith(prefix) for prefix in C_OWNED_PREFIXES)
    }
    assert changed_c_owned <= APPROVED_C_COMPATIBILITY_PATHS
    assert APPROVED_C_COMPATIBILITY_PATHS <= changed_c_owned


def test_d_does_not_touch_roadmap_or_reserved_pwa_otp_presentation() -> None:
    root = _root()
    for path in (*ROADMAP_PATHS, PWA_OTP_PRESENTATION):
        expected = _git_bytes(root, C_TAG, path)
        candidate = root / path
        if expected is None and not candidate.exists():
            continue
        assert expected is not None, f"D introduced protected path: {path}"
        assert candidate.is_file(), f"D removed protected path: {path}"
        assert candidate.read_bytes() == expected, f"D changed protected path: {path}"
