from datetime import datetime, timezone
from registries.metadata import (
    RegistryCapability, RegistryDataClassification, RegistryMetadataProfile,
    RegistryProvenance, RegistryRetention, RegistryTrainingEligibility,
)


def make_profile(
    *,
    capabilities=None,
    level="restricted",
    contains_personal=True,
    contains_sensitive=False,
    training_status="conditionally_eligible",
    anonymisation=True,
    aggregation=False,
    human_approval=False,
    consent=False,
    simulation_only=False,
    source_type="institution",
    generated=False,
    verified=False,
    production=False,
    simulation=True,
    retention_mode="permanent",
    retention_policy="",
    review_status="unreviewed",
):
    if capabilities is None:
        category = "simulation" if simulation else "identity"
        cap = RegistryCapability(
            "cap",
            "SIMULATION.SEED" if simulation else "IDENTITY.REGISTER",
            "Capability",
            category,
            supported=True,
            simulation_supported=simulation,
            production_supported=production,
        )
        capabilities = (cap,)
    classification = RegistryDataClassification(
        level,
        "Classification policy",
        contains_personal_data=contains_personal,
        contains_sensitive_personal_data=contains_sensitive,
        masking_required=level != "public",
    )
    kwargs = dict(
        anonymisation_required=anonymisation,
        aggregation_required=aggregation,
        human_approval_required=human_approval,
        consent_required=consent,
        simulation_only=simulation_only,
    )
    if training_status in {"eligible", "ineligible", "prohibited", "unreviewed"}:
        kwargs = dict(anonymisation_required=False, aggregation_required=False,
                      human_approval_required=False, consent_required=False,
                      simulation_only=False)
    provenance_kwargs = {}
    if source_type == "unknown":
        provenance_kwargs["reason"] = "Origin not yet established"
        source_system = ""
    else:
        source_system = "source"
    if generated:
        provenance_kwargs["generator_name"] = "generator"
    if verified:
        provenance_kwargs["verification_reference"] = "verification-1"
    provenance = RegistryProvenance(
        source_type,
        source_system,
        generated=generated,
        verified=verified,
        **provenance_kwargs,
    )
    retention = RegistryRetention(
        retention_mode,
        "Retention policy",
        policy_reference=retention_policy,
    )
    reviewed_at = None if review_status == "unreviewed" else datetime.now(timezone.utc)
    return RegistryMetadataProfile(
        "registry",
        capabilities,
        classification,
        RegistryTrainingEligibility(training_status, "Training policy", **kwargs),
        provenance,
        retention,
        review_status=review_status,
        reviewed_at=reviewed_at,
    )
