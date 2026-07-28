from registries.metadata import *

def make_profile(*, level="restricted", status="conditionally_eligible", generated=False, simulation_cap=True):
    cap = RegistryCapability("cap", "simulation.seed" if simulation_cap else "identity.register", "Capability", "simulation" if simulation_cap else "identity")
    classification = RegistryDataClassification(level, "Policy", contains_personal_data=level != "public", contains_sensitive_personal_data=level in {"confidential","highly_restricted"}, masking_required=level != "public")
    training = RegistryTrainingEligibility(status, "Training policy", anonymisation_required=status == "conditionally_eligible")
    provenance = RegistryProvenance("simulation_generator" if generated else "institution", "source", generated=generated, generator_name="gen" if generated else "")
    retention = RegistryRetention("permanent", "History")
    return RegistryMetadataProfile("registry", (cap,), classification, training, provenance, retention)

def test_validator_accepts_coherent_profile():
    result = RegistryMetadataValidator().validate(make_profile())
    assert result.valid and result.metadata["registry_id"] == "registry"

def test_validator_rejects_confidential_unconditional_training():
    result = RegistryMetadataValidator().validate(make_profile(level="confidential", status="eligible"))
    assert result.invalid
    assert result.errors[0].code == "REGISTRY_METADATA_TRAINING_CLASSIFICATION_CONFLICT"

def test_validator_rejects_generated_profile_without_simulation_capability():
    result = RegistryMetadataValidator().validate(make_profile(generated=True, simulation_cap=False))
    assert result.invalid
