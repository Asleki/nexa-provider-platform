from datetime import datetime, timezone
import pytest
from registries.metadata import *

def components(*, generated=False):
    cap = RegistryCapability("cap", "simulation.seed" if generated else "identity.register", "Capability", "simulation" if generated else "identity")
    classification = RegistryDataClassification("restricted", "Registry data", contains_personal_data=True, masking_required=True)
    training = RegistryTrainingEligibility("conditionally_eligible", "Controlled use", anonymisation_required=True)
    provenance = RegistryProvenance("simulation_generator" if generated else "institution", "civil-registry", generated=generated, generator_name="generator" if generated else "")
    retention = RegistryRetention("permanent", "Legal history", archive_required=True)
    return cap, classification, training, provenance, retention

def test_profile_is_immutable_deterministic_aggregate():
    cap, classification, training, provenance, retention = components()
    profile = RegistryMetadataProfile("citizen-registry", (cap,), classification, training, provenance, retention)
    assert profile.to_dict()["registry_id"] == "citizen-registry"
    assert profile.to_dict() == profile.to_dict()

def test_profile_rejects_duplicate_capability_codes():
    cap, classification, training, provenance, retention = components()
    cap2 = RegistryCapability("cap2", cap.capability_code, "Other", cap.category)
    with pytest.raises(RegistryMetadataProfileError): RegistryMetadataProfile("r", (cap, cap2), classification, training, provenance, retention)
