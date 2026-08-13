import pytest
from registries.nngla.source import load_identifier_catalogue
from registries.nngla.spatial_identifiers import SpatialIdentifierFormat

def test_source_catalogue_preserves_namespaces_and_registered_formats():
    cat = load_identifier_catalogue()
    assert len(cat.namespaces) == 11
    assert len(cat.formats) == 28
    assert all(n.immutable_after_issue and not n.reusable_after_retirement for n in cat.namespaces)
    assert all(f.immutable and not f.runtime_scoped for f in cat.formats)
    assert all(f.validates(f.example_identifier) for f in cat.formats)

def test_format_driven_validation_handles_fixed_and_structured_identifiers():
    cat = load_identifier_catalogue()
    assert cat.format_for_family("ROAD").validates("NG-RD-000123")
    assert not cat.format_for_family("ROAD").validates("NG-RD-123")
    assert cat.format_for_family("PARCEL").validates("NV-12-004-8890")
    assert cat.format_for_family("GEOMETRY").validates("NG-GEO-999999")

def test_runtime_scoped_identifier_format_is_rejected():
    with pytest.raises(ValueError):
        SpatialIdentifierFormat("fmt:x","ns:x","X","X-",r"^X-\d$",1,True,"NONE","X-1",True,True,"NNGLA","ACTIVE")
