"""Contract tests for P001.2 — Repository, Frontend and Roadmap Governance."""

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]

DOCUMENT = (
    REPOSITORY_ROOT
    / "docs"
    / "pwa"
    / "PWA-002-repository-frontend-and-roadmap-governance.md"
)

PWA_ROADMAP_FILES = (
    REPOSITORY_ROOT / "PWA_ROADMAP.md",
    REPOSITORY_ROOT / "pwa_roadmap.py",
    REPOSITORY_ROOT / "pwa_roadmap_data.py",
    REPOSITORY_ROOT / "pwa_roadmap_frontend.py",
)

CANONICAL_BRAND_ROOT = (
    REPOSITORY_ROOT
    / "frontend"
    / "public"
    / "brand"
    / "nexilabs"
)


def _document_text() -> str:
    """Return the authoritative PWA-002 document text."""

    return DOCUMENT.read_text(encoding="utf-8")


def test_governance_document_exists() -> None:
    assert DOCUMENT.is_file()


def test_document_identity_and_parent_foundation_are_declared() -> None:
    text = _document_text()

    assert "# PWA-002 — Repository, Frontend and Roadmap Governance" in text
    assert "| Document ID | `PWA-002` |" in text
    assert (
        "| Parent foundation | "
        "`P001 — NexiLabs PWA Project Foundation` |"
    ) in text
    assert "| Repository | `nexa-provider-platform` |" in text
    assert "| Status | Normative foundation |" in text


def test_repository_is_the_existing_npp_monorepository() -> None:
    text = _document_text()

    assert "The PWA remains in the existing monorepository:" in text
    assert "nexa-provider-platform/" in text
    assert REPOSITORY_ROOT.name == "nexa-provider-platform"


def test_frontend_is_the_single_application_boundary() -> None:
    text = _document_text()

    assert "The current application boundary is:" in text
    assert "frontend/" in text
    assert (REPOSITORY_ROOT / "frontend").is_dir()

    prohibited_parallel_roots = (
        REPOSITORY_ROOT / "pwa",
        REPOSITORY_ROOT / "nexilabs-pwa",
        REPOSITORY_ROOT / "novegeo-pwa",
        REPOSITORY_ROOT / "web",
        REPOSITORY_ROOT / "client",
    )

    for path in prohibited_parallel_roots:
        assert not path.exists(), (
            f"unexpected competing frontend application root exists: {path}"
        )


def test_normative_pwa_documents_are_kept_under_docs_pwa() -> None:
    text = _document_text()
    docs_root = REPOSITORY_ROOT / "docs" / "pwa"

    assert "Normative PWA documents belong in:" in text
    assert "docs/pwa/" in text
    assert docs_root.is_dir()
    assert DOCUMENT.parent == docs_root


def test_pwa_roadmap_governance_files_remain_at_repository_root() -> None:
    text = _document_text()

    assert "PWA roadmap governance remains at repository root:" in text

    expected_names = (
        "PWA_ROADMAP.md",
        "pwa_roadmap.py",
        "pwa_roadmap_data.py",
        "pwa_roadmap_frontend.py",
    )

    for name in expected_names:
        assert name in text

    for path in PWA_ROADMAP_FILES:
        assert path.is_file(), f"missing PWA roadmap governance file: {path}"


def test_pwa_roadmap_data_is_canonical_and_markdown_is_generated() -> None:
    text = _document_text()

    assert "`pwa_roadmap_data.py` is the canonical roadmap source." in text
    assert "`PWA_ROADMAP.md` is generated output." in text
    assert (
        REPOSITORY_ROOT / "pwa_roadmap_data.py"
    ).is_file()
    assert (
        REPOSITORY_ROOT / "PWA_ROADMAP.md"
    ).is_file()


def test_pwa_roadmap_update_commands_are_declared() -> None:
    text = _document_text()

    required_commands = (
        "python pwa_roadmap_frontend.py",
        "python pwa_roadmap.py verify",
        "python pwa_roadmap_frontend.py --check",
    )

    for command in required_commands:
        assert command in text

    assert (
        "The main NPP roadmap generator is not used for "
        "PWA-only status changes."
    ) in text


def test_canonical_brand_assets_have_one_authoritative_location() -> None:
    text = _document_text()

    assert "The existing NexiLabs brand assets remain authoritative at:" in text
    assert "frontend/public/brand/nexilabs/" in text
    assert CANONICAL_BRAND_ROOT.is_dir()

    expected_directories = (
        "icons",
        "logos",
        "metadata",
        "pwa",
        "social",
        "vectors",
    )

    for directory_name in expected_directories:
        assert (
            CANONICAL_BRAND_ROOT / directory_name
        ).is_dir(), f"missing canonical brand directory: {directory_name}"


def test_no_duplicate_canonical_nexilabs_brand_root_exists() -> None:
    canonical = CANONICAL_BRAND_ROOT.resolve()

    matching_directories = tuple(
        path.resolve()
        for path in REPOSITORY_ROOT.rglob("nexilabs")
        if path.is_dir()
    )

    assert canonical in matching_directories

    duplicate_brand_roots = tuple(
        path
        for path in matching_directories
        if path != canonical
        and (
            (path / "logos").exists()
            or (path / "icons").exists()
            or (path / "vectors").exists()
        )
    )

    assert duplicate_brand_roots == (), (
        "duplicate canonical NexiLabs brand roots found: "
        f"{duplicate_brand_roots}"
    )


def test_frontend_structure_may_materialize_only_inside_frontend() -> None:
    text = _document_text()
    frontend_root = REPOSITORY_ROOT / "frontend"

    assert "## Reserved frontend structure" in text
    assert (
        "A directory should be created only when\n"
        "the active milestone introduces real code that owns that responsibility."
    ) in text

    allowed_frontend_children = {
        "index.html",
        "public",
        "src",
        "tests",
        "scripts",
        "dist",
        "styles",
        "sw.js",  # P003 service worker must remain at application scope root.
    }

    actual_children = {
        path.name
        for path in frontend_root.iterdir()
    }

    unexpected_children = actual_children - allowed_frontend_children

    assert not unexpected_children, (
        "unexpected top-level frontend paths found: "
        f"{sorted(unexpected_children)}"
    )


def test_executable_frontend_source_is_permitted_after_p002_begins() -> None:
    frontend_src = REPOSITORY_ROOT / "frontend" / "src"

    if frontend_src.exists():
        assert frontend_src.is_dir()

        permitted_source_directories = {
            "app",
            "branding",
            "config",
            "core",
            "map",
            "simulation",
            "styles",
            "ui",
            "pwa",  # P003 install, offline and update lifecycle ownership.
        }

        actual_source_directories = {
            path.name
            for path in frontend_src.iterdir()
            if path.is_dir()
        }

        unexpected_directories = (
            actual_source_directories - permitted_source_directories
        )

        assert not unexpected_directories, (
            "frontend source contains ungoverned directories: "
            f"{sorted(unexpected_directories)}"
        )


def test_frontend_source_does_not_escape_the_application_boundary() -> None:
    prohibited_source_roots = (
        REPOSITORY_ROOT / "src",
        REPOSITORY_ROOT / "app",
        REPOSITORY_ROOT / "branding",
        REPOSITORY_ROOT / "map",
        REPOSITORY_ROOT / "simulation",
        REPOSITORY_ROOT / "ui",
    )

    for path in prohibited_source_roots:
        assert not path.exists(), (
            f"PWA source responsibility escaped frontend/: {path}"
        )


def test_naming_rules_are_declared() -> None:
    text = _document_text()

    required_rules = (
        "directories use lowercase kebab-case or established lowercase names;",
        "Python files use lowercase snake_case;",
        "JavaScript modules use lowercase kebab-case;",
        "test names describe observable behaviour;",
        "generated output is not edited by hand;",
    )

    for rule in required_rules:
        assert rule in text


def test_cross_system_identifiers_remain_semantically_distinct() -> None:
    text = _document_text()

    assert (
        "map, layer, dataset, event, runtime, registry, and world-state "
        "identifiers"
    ) in text
    assert "must remain semantically distinct;" in text
    assert (
        "generic unqualified `id` fields are discouraged at "
        "cross-system boundaries."
    ) in text


def test_functional_milestones_must_create_real_capability() -> None:
    text = _document_text()

    assert "## Roadmap design rule" in text
    assert (
        "What executable or observable product capability exists "
        "after this milestone"
    ) in text
    assert "that did not exist before?" in text

    expected_capabilities = (
        "the application boots;",
        "branding renders;",
        "the manifest installs;",
        "the offline shell loads;",
        "the map displays;",
        "coordinates convert;",
        "terrain layers render;",
        "AWS deployment succeeds;",
        "an approved API query returns safe data.",
    )

    for capability in expected_capabilities:
        assert capability in text


def test_documentation_only_work_is_consolidated() -> None:
    text = _document_text()

    assert (
        "Documentation-only outcomes must be consolidated into "
        "foundation documents"
    ) in text
    assert "must not dominate the engineering roadmap." in text


def test_visible_numbers_and_stable_record_ids_are_distinct() -> None:
    text = _document_text()

    assert "Visible milestone numbers and stable record IDs serve different purposes." in text
    assert "visible numbers communicate sequence;" in text
    assert "stable record IDs preserve identity;" in text


def test_completed_milestones_are_immutable_except_for_maintenance() -> None:
    text = _document_text()

    assert "completed milestones are immutable except for verified maintenance;" in text
    assert (
        "semantic titles must not be casually renamed after completion;"
    ) in text
    assert (
        "roadmap restructuring must preserve completed evidence"
    ) in text


def test_locked_governance_outcome_is_declared() -> None:
    text = _document_text()

    assert "## Locked outcome" in text
    assert "one PWA application boundary" in text
    assert "one canonical brand location" in text
    assert "one PWA roadmap source" in text
    assert "one generated roadmap view" in text
    assert (
        "future milestones must produce real application capability "
        "rather than merely"
    ) in text
    assert "more documentation." in text