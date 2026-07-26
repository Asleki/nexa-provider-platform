import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CATALOGUES = ROOT / "registries" / "catalogues"


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return tuple(found)


def test_m008_7_catalogue_files_are_implemented():
    expected = {
        "__init__.py",
        "_definition_catalogue.py",
        "catalogue_errors.py",
        "identifier_catalogue.py",
        "namespace_catalogue.py",
        "registry_catalogue.py",
    }
    assert {path.name for path in CATALOGUES.glob("*.py")} == expected
    for path in CATALOGUES.glob("*.py"):
        assert path.stat().st_size > 0


def test_catalogues_respect_m008_7_boundaries():
    forbidden = (
        "registries.adapters",
        "registries.factories",
        "registries.governance",
        "registries.ports",
        "registries.relationships",
        "registries.validators",
        "shared.audit",
        "shared.events",
        "services",
        "backend",
        "database",
        "sync",
        "fastapi",
        "flask",
        "supabase",
    )
    violations = []
    for path in CATALOGUES.glob("*.py"):
        for imported in _imports(path):
            if imported.startswith(forbidden):
                violations.append(f"{path}: {imported}")
    assert violations == []


def test_catalogue_is_not_repository_factory_lifecycle_event_or_api_layer():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in CATALOGUES.glob("*.py"))
    forbidden_fragments = (
        "MemoryRegistryRepository",
        "RegistryRepositoryFactory",
        "publish_event",
        "audit_record",
        "@app.",
        "APIRouter",
        "transition_status",
        "unregister(",
        "replace=True",
    )
    for fragment in forbidden_fragments:
        assert fragment not in combined


def test_previous_m008_boundary_tests_remain_present():
    folder = ROOT / "tests" / "unit" / "registries"
    for number in range(1, 7):
        assert list(folder.glob(f"test_m008_{number}_*_boundaries.py"))
