"""P006.UI.10.2.C — immutable B-prefix and no-roadmap compatibility qualification."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest


B_TAG = "P006.UI.10.2.B-governed-enigma-catalogue-admission"
MANIFEST_PATH = "database/migrations/migration_manifest.json"
C_MIGRATION_ID = "m006_10_02_layered_admin_review_authority"
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
LOCKED_B_PRODUCTION_PATHS = (
    "backend/auth/enigma_catalogue_admission/__init__.py",
    "backend/auth/enigma_catalogue_admission/contracts.py",
    "backend/auth/enigma_catalogue_admission/postgresql.py",
    "backend/auth/enigma_catalogue_admission/service.py",
    "backend/auth/enigma_catalogue_admission/source.py",
    "verification/auth/p006_ui_10_2_b_enigma_catalogue_admission.py",
)


def _root() -> Path:
    here = Path(__file__).resolve()
    for candidate in [here.parent, *here.parents]:
        if (candidate / ".git").exists() and (candidate / "database/migrations").is_dir():
            return candidate
    pytest.skip("git-backed repository required for predecessor lock proof")


def _git_bytes(root: Path, revision: str, path: str) -> bytes | None:
    proc = subprocess.run(
        ["git", "show", f"{revision}:{path}"],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return proc.stdout if proc.returncode == 0 else None


def test_c_manifest_is_exactly_one_governed_append_after_b() -> None:
    root = _root()
    b_raw = _git_bytes(root, B_TAG, MANIFEST_PATH)
    assert b_raw is not None, "B annotated tag manifest is unavailable"
    before = json.loads(b_raw.decode("utf-8"))
    current = json.loads((root / MANIFEST_PATH).read_text(encoding="utf-8"))
    assert current["manifest_schema"] == before["manifest_schema"]
    assert current["manifest_schema_version"] == before["manifest_schema_version"]
    assert current["catalogue_version"] == before["catalogue_version"] + 1
    assert len(current["migrations"]) == len(before["migrations"]) + 1
    assert current["migrations"][:-1] == before["migrations"]
    assert current["migrations"][-1]["migration_id"] == C_MIGRATION_ID
    assert current["migrations"][-1]["sequence_number"] == 32


def test_c_does_not_rewrite_locked_b_production_modules() -> None:
    root = _root()
    for path in LOCKED_B_PRODUCTION_PATHS:
        expected = _git_bytes(root, B_TAG, path)
        assert expected is not None, path
        assert (root / path).read_bytes() == expected, path


def test_c_does_not_touch_roadmap_authority() -> None:
    root = _root()
    for path in ROADMAP_PATHS:
        expected = _git_bytes(root, B_TAG, path)
        candidate = root / path
        if expected is None and not candidate.exists():
            continue
        assert expected is not None, f"C introduced roadmap path: {path}"
        assert candidate.is_file(), f"C removed roadmap path: {path}"
        assert candidate.read_bytes() == expected, f"C changed roadmap path: {path}"
