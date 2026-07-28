import pytest
from registries.metadata import RegistryCapability, RegistryCapabilityCategory, RegistryCapabilityError

def test_capability_normalizes_and_round_trips():
    cap = RegistryCapability(" cap-1 ", " simulation.seed ", " Seed Registry ", "simulation", production_supported=False)
    assert cap.capability_id == "cap-1" and cap.capability_code == "SIMULATION.SEED"
    assert cap.category is RegistryCapabilityCategory.SIMULATION
    assert RegistryCapability.from_dict(cap.to_dict()) == cap

def test_capability_rejects_runtime_support_without_supported():
    with pytest.raises(RegistryCapabilityError): RegistryCapability("a", "b", "c", "identity", supported=False, simulation_supported=True)
