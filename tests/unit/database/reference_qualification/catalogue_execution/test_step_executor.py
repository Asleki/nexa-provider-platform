from database.reference_qualification.catalogue_execution.step_executor import classify
from registries.name_authority.production_context import NameStructureType

def test_structure_classifier_preserves_structural_forms():
    assert classify("José") is NameStructureType.SIMPLE
    assert classify("García Hernández") is NameStructureType.COMPOUND_SPACE_SEPARATED
    assert classify("Van der Berg") is NameStructureType.PREFIXED_COMPOUND
    assert classify("Smith-Jones") is NameStructureType.HYPHENATED
    assert classify("O'Connor") is NameStructureType.APOSTROPHIZED
