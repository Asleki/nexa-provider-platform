"""Contract tests for P002.3 and P002.4 brand and application shell."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
FRONTEND = ROOT / "frontend"
BRAND_ROOT = FRONTEND / "public" / "brand" / "nexilabs"


def _text(relative: str) -> str:
    return (FRONTEND / relative).read_text(encoding="utf-8")


def test_brand_and_shell_files_exist() -> None:
    for relative in (
        "src/branding/brand-assets.js",
        "src/branding/brand-config.js",
        "tests/brand-assets.test.mjs",
        "tests/application-shell.test.mjs",
    ):
        assert (FRONTEND / relative).is_file(), relative


def test_canonical_brand_package_is_consumed_not_duplicated() -> None:
    html = _text("index.html")
    assets = _text("src/branding/brand-assets.js")
    assert "./public/brand/nexilabs/metadata/brand-tokens.css" in html
    assert "./public/brand/nexilabs/vectors/nexilabs_logo_horizontal.svg" in html
    assert 'const BRAND_ROOT = "./public/brand/nexilabs"' in assets
    assert (BRAND_ROOT / "vectors" / "nexilabs_logo_horizontal.svg").is_file()
    assert (BRAND_ROOT / "metadata" / "brand-tokens.css").is_file()


def test_html_retains_runtime_contract_and_adds_semantic_shell() -> None:
    html = _text("index.html")
    for marker in (
        'id="nexilabs-app"',
        'data-role="application-status"',
        'data-role="runtime-mode"',
        'data-role="application-version"',
        '<header class="application-header"',
        '<main id="main-content"',
        '<footer class="application-footer"',
        'class="skip-link"',
    ):
        assert marker in html


def test_shell_has_no_external_first_render_dependency() -> None:
    html = _text("index.html")
    assert "https://" not in html
    assert "http://" not in html
    assert "cdn" not in html.lower()
    assert html.count("<script") == 1


def test_brand_application_contract_is_immutable_and_optional() -> None:
    source = _text("src/branding/brand-config.js")
    assert "Object.freeze" in source
    assert "[data-role='brand-logo']" in source
    assert "[data-role='brand-name']" in source
    assert "if (logo)" in source
    assert "if (brandName)" in source


def test_application_bootstrap_applies_brand_without_replacing_lifecycle() -> None:
    source = _text("src/app/application.js")
    assert "applyBrand(documentRef)" in source
    for status in ("ApplicationStatus.BOOTING", "ApplicationStatus.READY", "ApplicationStatus.FAILED"):
        assert status in source
    assert "brand: brandReceipt" in source


def test_styles_derive_from_canonical_tokens_and_are_responsive() -> None:
    css = _text("styles/app.css")
    for marker in (
        "var(--nexilabs-navy)",
        "var(--nexilabs-cyan)",
        "var(--nexilabs-teal)",
        "@media (max-width: 56rem)",
        "@media (max-width: 40rem)",
        "@media (prefers-reduced-motion: reduce)",
        ":focus-visible",
    ):
        assert marker in css


def test_shell_does_not_claim_deferred_capabilities() -> None:
    html = _text("index.html")
    normalized = " ".join(html.split())
    assert "Interaction, registry overlays and dynamic simulation remain deferred." in normalized
    for prohibited in ("serviceWorker.register", "navigator.serviceWorker", "postgresql://", "rds.amazonaws.com"):
        assert prohibited not in html
