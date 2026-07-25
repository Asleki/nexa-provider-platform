import ast
from pathlib import Path

FILES = (
    Path("registries/core/identifier_definition.py"),
    Path("registries/core/identifier_lifecycle.py"),
    Path("registries/core/identifier_reference.py"),
    Path("registries/core/namespace_definition.py"),
    Path("registries/core/numbering_strategy.py"),
)
FORBIDDEN = (
    "registries.adapters", "registries.catalogues", "registries.governance",
    "registries.ports", "registries.validators", "shared.audit", "shared.events",
    "database", "services", "backend", "sync", "requests", "httpx", "supabase",
)


def _imports(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            out.append(node.module)
    return out


def test_m008_2_models_respect_domain_boundaries():
    violations = []
    for path in FILES:
        for imported in _imports(path):
            if imported.startswith(FORBIDDEN):
                violations.append(f"{path}: {imported}")
    assert violations == []
