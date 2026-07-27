import ast
from pathlib import Path

from registries.events import RegistryEvent, RegistryEventFactory, RegistryEventType
from shared.events import BaseEvent

ROOT = Path(__file__).resolve().parents[3]
EVENTS = ROOT / "registries" / "events"


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return tuple(found)


def test_m008_10_appends_tests_without_removing_previous_boundaries():
    registry_tests = ROOT / "tests" / "unit" / "registries"
    for milestone in range(1, 10):
        assert list(registry_tests.glob(f"test_m008_{milestone}_*boundaries.py"))


def test_registry_events_extend_shared_m006_event_infrastructure():
    assert issubclass(RegistryEvent, BaseEvent)
    assert RegistryEventType.REGISTRY_REGISTERED.value.startswith("registry.")


def test_registry_events_do_not_create_a_parallel_bus_or_persistence_layer():
    combined = "\n".join(path.read_text() for path in EVENTS.glob("*.py"))
    forbidden = (
        "class RegistryEventBus",
        "publish(",
        "repository.add",
        "MemoryEventRepository",
        "AuditRepository",
        "APIRouter",
        "FastAPI",
        "supabase",
    )
    for token in forbidden:
        assert token not in combined


def test_registry_event_import_boundaries_are_clean():
    forbidden_prefixes = (
        "registries.adapters",
        "registries.catalogues",
        "registries.factories",
        "services",
        "backend",
        "database",
        "sync",
        "shared.audit",
    )
    violations = []
    for path in EVENTS.glob("*.py"):
        for imported in _imports(path):
            if imported.startswith(forbidden_prefixes):
                violations.append(f"{path.name}: {imported}")
    assert violations == []


def test_event_factory_only_constructs_and_does_not_execute_side_effects():
    source = (EVENTS / "registry_event_factory.py").read_text()
    assert "class RegistryEventFactory" in source
    for token in (".save(", ".add(", ".publish(", ".process(", "audit"):
        assert token not in source.lower()


def test_later_m008_api_audit_metadata_and_relationship_layers_remain_absent():
    for folder in ("api", "apis", "metadata"):
        path = ROOT / "registries" / folder
        assert not path.exists() or not any(path.glob("*.py"))
