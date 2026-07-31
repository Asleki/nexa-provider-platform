from registries.names import CanonicalName,NameKind,NameMetadata
from registries.names.name_sex_usage_metadata import with_name_sex_usage
from registries.name_suggestions.full_name_sex_compatibility import evaluate_full_name_sex_compatibility
from registries.name_suggestions.name_sex_compatibility_outcome import NameSexCompatibilityOutcome as O
def n(i,k,u): return CanonicalName(i,i,k,with_name_sex_usage(NameMetadata(),u))
def test_component_evidence_and_conflict_precedence():
    result=evaluate_full_name_sex_compatibility("male",(n("Alex",NameKind.FIRST_NAME,"unisex"),n("Grace",NameKind.MIDDLE_NAME,"female"),n("Mwangi",NameKind.SURNAME,"unspecified")))
    assert result.outcome is O.CONFLICT and len(result.components)==3
