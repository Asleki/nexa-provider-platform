from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).parents[3]
MEMORY_PACKAGE = ROOT / "registries" / "adapters" / "memory"
IMPLEMENTATION = MEMORY_PACKAGE / "memory_registry_repository.py"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_memory_repository_is_outside_ports() -> None:
    assert IMPLEMENTATION.exists()
    assert not (
        ROOT / "registries" / "ports" / "memory_registry_repository.py"
    ).exists()


def test_m008_5_imports_only_approved_layers() -> None:
    modules = imported_modules(IMPLEMENTATION)
    forbidden = (
        "shared.events",
        "shared.audit",
        "registries.governance",
        "registries.catalogues",
        "registries.validators",
        "database",
        "storage",
        "sqlite3",
        "json",
        "csv",
        "supabase",
        "services",
        "backend",
        "requests",
        "urllib",
        "http",
    )
    assert not any(module.startswith(forbidden) for module in modules), modules
    assert "threading" in modules
    assert any(module.startswith("registries.ports") for module in modules)


def test_no_module_level_repository_singleton() -> None:
    tree = ast.parse(IMPLEMENTATION.read_text(encoding="utf-8"))
    assignments = [
        node
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and not (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name) and target.id == "__all__"
                for target in node.targets
            )
        )
    ]
    assert assignments == []


def test_all_m008_4_operations_are_implemented() -> None:
    tree = ast.parse(IMPLEMENTATION.read_text(encoding="utf-8"))
    repository_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "MemoryRegistryRepository"
    )
    methods = {
        node.name for node in repository_class.body
        if isinstance(node, ast.FunctionDef)
    }
    assert {
        "add", "get", "replace", "remove",
        "list_all", "exists", "count", "clear",
    }.issubset(methods)


def test_no_event_audit_file_or_transport_calls() -> None:
    source = IMPLEMENTATION.read_text(encoding="utf-8").lower()
    forbidden = (
        "publish(",
        "audit(",
        "requests.",
        "httpx.",
        "supabase.",
        "open(",
        "sqlite3.",
    )
    assert all(token not in source for token in forbidden)
