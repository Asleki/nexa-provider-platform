from __future__ import annotations

import ast
from pathlib import Path


BASE_REGISTRY_PATH = (
    Path(__file__).parents[3]
    / "registries"
    / "core"
    / "base_registry.py"
)


def imported_modules() -> set[str]:
    tree = ast.parse(BASE_REGISTRY_PATH.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def test_base_registry_stays_inside_m008_3_boundaries() -> None:
    forbidden_prefixes = (
        "registries.repositories",
        "registries.ports",
        "registries.adapters",
        "registries.catalogues",
        "registries.validators",
        "registries.governance",
        "shared.events",
        "shared.audit",
        "storage",
        "database",
        "services",
    )
    assert not any(
        module.startswith(forbidden_prefixes)
        for module in imported_modules()
    )


def test_base_registry_has_no_future_milestone_actions() -> None:
    tree = ast.parse(BASE_REGISTRY_PATH.read_text(encoding="utf-8"))
    method_names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    forbidden = {
        "save",
        "delete",
        "activate",
        "suspend",
        "retire",
        "issue_identifier",
        "allocate_identifier",
        "publish_event",
        "write_audit",
    }
    assert method_names.isdisjoint(forbidden)
