import inspect
from registries.names import NameRepository

def test_repository_contract_is_abstract_and_storage_neutral():
    assert inspect.isabstract(NameRepository)
    assert {"add","get","replace","exists","count","list_all","search"} <= set(NameRepository.__abstractmethods__)
