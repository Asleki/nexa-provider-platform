import ast
from pathlib import Path


CONTRACT_PACKAGE = Path("registries/contracts")
FORBIDDEN_PREFIXES = (
    "registries.adapters",
    "registries.catalogues",
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
)


def _imports(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
    return tuple(found)


def test_registry_contract_package_respects_m008_1_boundaries():
    violations: list[str] = []
    for path in sorted(CONTRACT_PACKAGE.glob("*.py")):
        for imported in _imports(path):
            if imported.startswith(FORBIDDEN_PREFIXES):
                violations.append(f"{path}: {imported}")
    assert violations == []
