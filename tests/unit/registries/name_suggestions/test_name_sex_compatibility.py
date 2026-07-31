from registries.names import CanonicalName,NameKind,NameMetadata
from registries.names.name_sex_usage_metadata import with_name_sex_usage
from registries.name_suggestions.name_sex_compatibility import evaluate_name_sex_compatibility
from registries.name_suggestions.name_sex_compatibility_outcome import NameSexCompatibilityOutcome as O
def n(i,u): return CanonicalName(i,i,NameKind.FIRST_NAME,with_name_sex_usage(NameMetadata(),u))
def test_compatible_conflict_and_unisex():
    assert evaluate_name_sex_compatibility("male",n("John","male")).outcome is O.COMPATIBLE
    assert evaluate_name_sex_compatibility("male",n("Grace","female")).outcome is O.CONFLICT
    assert evaluate_name_sex_compatibility("female",n("Alex","unisex")).outcome is O.COMPATIBLE
def test_intersex_is_ambiguous_for_binary_usage(): assert evaluate_name_sex_compatibility("intersex",n("John","male")).outcome is O.AMBIGUOUS
