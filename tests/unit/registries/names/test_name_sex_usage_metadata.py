import pytest
from registries.names import NameMetadata
from registries.names.name_sex_usage import NameSexUsage
from registries.names.name_sex_usage_metadata import read_name_sex_usage,with_name_sex_usage
from registries.names.name_sex_usage_errors import NameSexUsageMetadataError
def test_round_trip_preserves_existing_attributes():
    original=NameMetadata(attributes={"source":{"quality":"reviewed"}})
    enriched=with_name_sex_usage(original,NameSexUsage.FEMALE)
    assert read_name_sex_usage(enriched) is NameSexUsage.FEMALE
    assert enriched.attributes["source"]["quality"]=="reviewed"
    assert read_name_sex_usage(original) is NameSexUsage.UNSPECIFIED
def test_rejects_reserved_namespace_wrong_shape():
    with pytest.raises(NameSexUsageMetadataError): read_name_sex_usage(NameMetadata(attributes={"name_usage":"bad"}))
