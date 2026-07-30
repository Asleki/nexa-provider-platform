import registries.names as names

def test_public_exports_are_complete_and_stable():
    required={"CanonicalName","FirstName","MiddleName","Surname","NameKind","NameStatus","NameMetadata","NameRepository","MemoryNameRepository","NameSearchQuery","NameSearchResult","NameSearchService"}
    assert required <= set(names.__all__)
    for symbol in required: assert hasattr(names,symbol)
