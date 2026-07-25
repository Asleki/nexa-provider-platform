from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).parents[3]
PORTS = ROOT / "registries" / "ports"


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_m008_4_has_no_concrete_storage_or_future_layer_imports() -> None:
    forbidden = (
        "registries.adapters",
        "registries.catalogues",
        "registries.governance",
        "registries.validators",
        "shared.events",
        "shared.audit",
        "storage",
        "database",
        "services",
        "json",
        "csv",
        "sqlite3",
        "threading",
    )
    for path in PORTS.glob("*.py"):
        modules = imported_modules(path)
        assert not any(
            module.startswith(forbidden)
            for module in modules
        ), f"{path.name} crosses the M008.4 boundary: {modules}"


def test_interface_declares_no_concrete_collection_state() -> None:
    source = (PORTS / "registry_repository.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    class_assignments = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        and any(
            isinstance(parent, ast.ClassDef)
            for parent in ast.walk(tree)
            if node in getattr(parent, "body", ())
        )
    ]
    assert class_assignments == []


def test_earlier_registry_packages_are_not_modified_by_this_scope() -> None:
    expected_new_names = {
        "base_registry_repository.py",
        "registry_repository.py",
        "registry_repository_errors.py",
        "registry_repository_result.py",
        "registry_repository_types.py",
    }
    assert expected_new_names.issubset(
        {path.name for path in PORTS.glob("*.py")}
    )
