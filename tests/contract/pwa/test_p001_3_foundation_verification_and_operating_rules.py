"""Contract tests for P001.3 — Foundation Verification and Operating Rules."""
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
DOCUMENT = REPOSITORY_ROOT / "docs" / "pwa" / "PWA-003-foundation-verification-and-operating-rules.md"


def _text() -> str:
    return DOCUMENT.read_text(encoding="utf-8")


def test_operating_rules_document_exists() -> None:
    assert DOCUMENT.is_file()
    assert "PWA-003" in _text()


def test_foundation_verification_commands_are_declared() -> None:
    text = _text()
    assert "python pwa_roadmap.py verify" in text
    assert "python pwa_roadmap_frontend.py --check" in text
    assert "python -m compileall" in text


def test_functional_milestone_acceptance_requires_real_capability() -> None:
    text = _text()
    assert "introduces a real production capability" in text
    assert "matching tests verify observable behaviour" in text
    assert "full repository regression passes" in text
    assert "implementation and roadmap update are committed together" in text


def test_document_word_search_is_not_sufficient_engineering_evidence() -> None:
    text = _text()
    assert "only searches a Markdown document for expected words is not enough" in text
    assert "documentation existence alone is not a PWA capability" in text


def test_delivery_package_and_changelog_rules_are_present() -> None:
    text = _text()
    for filename in (
        "PLACEMENT_GUIDE.txt",
        "IMPLEMENTATION_SUMMARY.txt",
        "REFERENCE_FILES.txt",
        "TEST_COMMANDS.txt",
        "TEST_RESULTS.txt",
        "CHANGELOG.txt",
    ):
        assert filename in text


def test_milestone_immutability_is_declared() -> None:
    text = _text()
    assert "no feature additions to the locked milestone" in text
    assert "no API redesign" in text
    assert "New functionality must arrive through later modules" in text


def test_security_checks_are_reserved_for_executable_milestones() -> None:
    text = _text()
    for phrase in (
        "no database credentials in browser bundles",
        "no direct PostgreSQL or RDS endpoints",
        "HTTPS-only production API bases",
        "explicit runtime mode",
        "service-worker cache boundaries",
    ):
        assert phrase in text


def test_roadmap_restructuring_preserves_completed_work() -> None:
    text = _text()
    assert "preserve completed factual work" in text
    assert "remove redundant planned items" in text
    assert "replace them with capability-oriented milestones" in text
