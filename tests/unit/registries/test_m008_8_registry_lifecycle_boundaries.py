import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE = ROOT / "registries" / "governance"


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return tuple(found)


def test_m008_8_lifecycle_files_are_implemented_without_future_placeholders():
    expected_implemented = {
        "__init__.py",
        "lifecycle_errors.py",
        "lifecycle_policy.py",
        "lifecycle_result.py",
        "registry_lifecycle.py",
    }
    implemented = {
        path.name
        for path in GOVERNANCE.glob("*.py")
        if path.stat().st_size > 0
    }
    assert implemented == expected_implemented


def test_lifecycle_respects_m008_8_import_boundaries():
    forbidden = (
        "registries.adapters",
        "registries.catalogues",
        "registries.factories",
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
    for path in GOVERNANCE.glob("*.py"):
        if path.stat().st_size == 0:
            continue
        for imported in _imports(path):
            if imported.startswith(forbidden):
                violations.append(f"{path}: {imported}")
    assert violations == []


def test_lifecycle_is_not_event_audit_api_authorization_or_cascade_layer():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in GOVERNANCE.glob("*.py")
        if path.stat().st_size > 0
    )
    forbidden_fragments = (
        "publish_event",
        "audit_record",
        "APIRouter",
        "@app.",
        "permission_required",
        "approval_queue",
        "cascade_transition",
        "repository.replace",
        "MemoryRegistryRepository",
    )
    for fragment in forbidden_fragments:
        assert fragment not in combined


def test_lifecycle_reuses_existing_registry_status_and_base_registry():
    lifecycle = (GOVERNANCE / "registry_lifecycle.py").read_text(encoding="utf-8")
    policy = (GOVERNANCE / "lifecycle_policy.py").read_text(encoding="utf-8")
    assert "BaseRegistry" in lifecycle
    assert "RegistryDefinition" in lifecycle
    assert "RegistryStatus" in policy
    assert "class RegistryStatus" not in policy


def test_previous_m008_boundary_tests_remain_present():
    folder = ROOT / "tests" / "unit" / "registries"
    for number in range(1, 8):
        assert list(folder.glob(f"test_m008_{number}_*_boundaries.py"))
