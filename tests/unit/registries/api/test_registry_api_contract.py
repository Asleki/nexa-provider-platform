import pytest
from registries.api import RegistryApiContract, RegistryApiContractError

def test_contract_declares_all_supported_operations():
    contract=RegistryApiContract()
    assert contract.supports("register") and not contract.supports("clear")
    assert contract.to_dict()["name"]=="registry"

def test_contract_rejects_duplicate_operations():
    with pytest.raises(RegistryApiContractError): RegistryApiContract(operations=("get","get"))
