"""Contract tests for P001.2 — Repository, Frontend and Roadmap Governance."""
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENT = REPOSITORY_ROOT / "docs" / "pwa" / "PWA-002-repository-frontend-and-roadmap-governance.md"
BRAND_ROOT = REPOSITORY_ROOT / "frontend" / "public" / "brand" / "nexilabs"


def _text() -> str:
    return DOCUMENT.read_text(encoding="utf-8")


def test_governance_document_and_canonical_roots_exist() -> None:
    assert DOCUMENT.is_file()
    assert BRAND_ROOT.is_dir()
    for filename in (
        "PWA_ROADMAP.md",
        "pwa_roadmap.py",
        "pwa_roadmap_data.py",
        "pwa_roadmap_frontend.py",
    ):
        assert (REPOSITORY_ROOT / filename).is_file()


def test_document_consolidates_administrative_foundation() -> None:
    text = _text()
    assert "PWA-002" in text
    assert "combines the repository placement, naming, frontend-boundary" in text
    assert "not independent product\ncapabilities" in text


def test_repository_and_document_placement_are_canonical() -> None:
    text = _text()
    assert "nexa-provider-platform/" in text
    assert "frontend/" in text
    assert "docs/pwa/" in text


def test_brand_assets_have_one_canonical_location() -> None:
    text = _text()
    assert "frontend/public/brand/nexilabs/" in text
    assert "rather than create duplicate\ncanonical copies" in text
    assert not (REPOSITORY_ROOT / "brand" / "nexilabs").exists()


def test_frontend_structure_is_reserved_not_prematurely_materialized() -> None:
    text = _text()
    assert "Reserved frontend structure" in text
    assert "A directory should be created only when" in text
    assert not (REPOSITORY_ROOT / "frontend" / "src").exists()
    assert not (REPOSITORY_ROOT / "frontend" / "index.html").exists()


def test_naming_rules_preserve_semantic_identifiers() -> None:
    text = _text()
    assert "Python files use lowercase snake_case" in text
    assert "JavaScript modules use lowercase kebab-case" in text
    assert "generic unqualified `id` fields are discouraged" in text


def test_roadmap_source_and_generated_output_are_distinct() -> None:
    text = _text()
    assert "`pwa_roadmap_data.py` is the canonical roadmap source" in text
    assert "`PWA_ROADMAP.md` is generated output" in text
    assert "python pwa_roadmap_frontend.py" in text
    assert "python pwa_roadmap.py verify" in text


def test_capability_oriented_milestone_rule_is_declared() -> None:
    text = _text()
    assert "What executable or observable product capability exists" in text
    for phrase in (
        "the application boots",
        "the map displays",
        "AWS deployment succeeds",
        "an approved API query returns safe data",
    ):
        assert phrase in text


def test_completed_semantic_identity_is_protected() -> None:
    text = _text()
    assert "stable record IDs preserve identity" in text
    assert "must not be casually renamed after completion" in text
    assert "preserve completed evidence" in text
