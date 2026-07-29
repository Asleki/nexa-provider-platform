import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PRODUCTION = ROOT / "registries" / "relationships"
TESTS = ROOT / "tests" / "unit" / "registries" / "relationships"

REQUIRED_PRODUCTION = {
    "registry_reference.py", "relationship_type.py", "relationship_definition.py",
    "immutable_reference_result.py", "immutable_reference_rules.py",
    "direction_contract.py", "relationship_direction_rules.py",
    "constraint_contract.py", "relationship_constraint_rules.py",
    "provenance_contract.py", "relationship_provenance_rules.py",
    "relationship_api_contract.py", "relationship_validation_api.py",
}
FORBIDDEN_PRODUCTION = {
    "relationship_repository.py", "relationship_graph.py", "relationship_lifecycle.py",
    "relationship_event_factory.py", "relationship_command_handler.py",
    "relationship_direction.py", "relationship_constraint.py", "relationship_provenance.py", "relationship_api.py",
}
FORBIDDEN_IMPORT_ROOTS = {"fastapi", "flask", "django", "strawberry", "graphene", "sqlalchemy", "supabase", "psycopg", "requests", "httpx"}


def test_all_completed_relationship_production_families_exist():
    assert REQUIRED_PRODUCTION <= {path.name for path in PRODUCTION.glob("*.py")}


def test_forbidden_future_engines_remain_absent():
    assert not (FORBIDDEN_PRODUCTION & {path.name for path in PRODUCTION.glob("*.py")})


def test_relationship_production_remains_framework_and_storage_neutral():
    imported = set()
    for path in PRODUCTION.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
    assert not (FORBIDDEN_IMPORT_ROOTS & imported)


def test_all_m008_16_test_families_remain_present_with_new_integration_suite():
    required = {
        "test_registry_reference.py", "test_relationship_type.py", "test_relationship_definition.py",
        "test_immutable_reference_result.py", "test_immutable_reference_rules.py",
        "test_direction_contract.py", "test_relationship_direction_rules.py",
        "test_constraint_contract.py", "test_relationship_constraint_rules.py",
        "test_provenance_contract.py", "test_relationship_provenance_rules.py",
        "test_relationship_api_contract.py", "test_relationship_validation_api.py",
        "test_relationship_foundation_boundaries.py",
    }
    assert required <= {path.name for path in TESTS.glob("test_*.py")}
    integration = TESTS / "integration"
    assert {
        "test_relationship_foundation_end_to_end.py",
        "test_relationship_foundation_failure_safety.py",
        "test_relationship_foundation_runtime_isolation.py",
        "test_relationship_foundation_determinism.py",
    } <= {path.name for path in integration.glob("test_*.py")}


def test_validation_api_explicitly_denies_persistence_and_approval_semantics():
    source = (PRODUCTION / "relationship_validation_api.py").read_text(encoding="utf-8")
    assert '"validation_only": True' in source
    assert '"persisted": False' in source
    assert '"approved": False' in source
