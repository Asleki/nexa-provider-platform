from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
RELATIONSHIPS = ROOT / "registries" / "relationships"
RELATIONSHIP_TESTS = ROOT / "tests" / "unit" / "registries" / "relationships"


def test_m008_16_1_implements_only_relationship_contract_files():
    required = {
        "__init__.py",
        "registry_reference.py",
        "relationship_type.py",
        "relationship_definition.py",
    }
    assert required <= {path.name for path in RELATIONSHIPS.glob("*.py")}


def test_m008_16_1_appends_relationship_tests():
    required = {
        "test_registry_reference.py",
        "test_relationship_type.py",
        "test_relationship_definition.py",
        "test_relationship_contract_serialization.py",
        "test_relationship_contract_immutability.py",
        "test_relationship_contract_identity_boundaries.py",
        "test_relationship_runtime_boundaries.py",
        "test_relationship_exports.py",
    }
    assert required <= {path.name for path in RELATIONSHIP_TESTS.glob("test_*.py")}


def test_m008_16_1_does_not_implement_deferred_relationship_engines():
    forbidden = {
        "relationship_repository.py",
        "relationship_direction.py",
        "relationship_constraint.py",
        "relationship_provenance.py",
        "relationship_api.py",
        "relationship_graph.py",
    }
    assert not forbidden & {path.name for path in RELATIONSHIPS.glob("*.py")}


def test_relationship_type_is_extensible_not_a_closed_enum():
    text = (RELATIONSHIPS / "relationship_type.py").read_text(encoding="utf-8")
    assert "class RelationshipType:" in text
    assert "class RelationshipType(str, Enum)" not in text
