"""Cross-contract validator for RegistryMetadataProfile."""
from __future__ import annotations
from .registry_metadata_profile import RegistryMetadataProfile
from .registry_classification_level import RegistryClassificationLevel
from .registry_training_eligibility_status import RegistryTrainingEligibilityStatus
from .registry_retention_mode import RegistryRetentionMode
from registries.validators.validation_collector import RegistryValidationCollector
from registries.validators.validation_message import RegistryValidationMessage, ValidationSeverity

class RegistryMetadataValidator:
    def validate(self, profile: RegistryMetadataProfile):
        if not isinstance(profile, RegistryMetadataProfile): raise TypeError("profile must be a RegistryMetadataProfile.")
        c = RegistryValidationCollector()
        def error(code, field, message):
            c.add(RegistryValidationMessage(severity=ValidationSeverity.ERROR, code=code, field=field, message=message))
        classification = profile.data_classification
        training = profile.training_eligibility
        retention = profile.retention
        if classification.level >= RegistryClassificationLevel.CONFIDENTIAL and training.status is RegistryTrainingEligibilityStatus.ELIGIBLE:
            error("REGISTRY_METADATA_TRAINING_CLASSIFICATION_CONFLICT", "training_eligibility.status", "Confidential or stronger registry data cannot be unconditionally training eligible.")
        if classification.contains_sensitive_personal_data and training.status is RegistryTrainingEligibilityStatus.CONDITIONALLY_ELIGIBLE and not (training.anonymisation_required or training.aggregation_required):
            error("REGISTRY_METADATA_SENSITIVE_TRAINING_CONDITION_REQUIRED", "training_eligibility", "Sensitive personal data requires anonymisation or aggregation before conditional eligibility.")
        if retention.mode is RegistryRetentionMode.PERMANENT and retention.deletion_permitted:
            error("REGISTRY_METADATA_RETENTION_CONFLICT", "retention.deletion_permitted", "Permanent retention cannot permit deletion.")
        if profile.provenance.generated and not any(cap.category.value == "simulation" for cap in profile.capabilities):
            error("REGISTRY_METADATA_GENERATED_WITHOUT_SIMULATION_CAPABILITY", "capabilities", "Generated simulation provenance requires at least one simulation capability.")
        if any(cap.production_supported for cap in profile.capabilities) and training.simulation_only:
            c.add(RegistryValidationMessage(severity=ValidationSeverity.WARNING, code="REGISTRY_METADATA_PRODUCTION_CAPABILITY_SIMULATION_TRAINING", field="training_eligibility.simulation_only", message="Profile has production-supported capabilities but training eligibility is simulation-only."))
        return c.build(metadata={"registry_id": profile.registry_id, "profile_version": profile.profile_version})

__all__ = ["RegistryMetadataValidator"]
