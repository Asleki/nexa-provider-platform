"""Deterministic cross-contract validation for registry metadata profiles.

The validator reads an immutable :class:`RegistryMetadataProfile` and reports
cross-component policy findings through the shared Registry Validation
Foundation.  It does not mutate metadata, authorise actors, verify external
sources, activate registries, execute training, enforce retention, or persist
validation results.
"""
from __future__ import annotations

from .registry_capability_category import RegistryCapabilityCategory
from .registry_classification_level import RegistryClassificationLevel
from .registry_metadata_profile import RegistryMetadataProfile
from .registry_metadata_validation_errors import InvalidRegistryMetadataError
from .registry_provenance_source_type import RegistryProvenanceSourceType
from .registry_retention_mode import RegistryRetentionMode
from .registry_training_eligibility_status import RegistryTrainingEligibilityStatus
from registries.validators.validation_collector import RegistryValidationCollector
from registries.validators.validation_message import (
    RegistryValidationMessage,
    ValidationSeverity,
)
from registries.validators.validation_result import RegistryValidationResult


class RegistryMetadataValidator:
    """Read-only deterministic validator for one aggregate metadata profile."""

    VERSION = 1

    @classmethod
    def validate(cls, profile: RegistryMetadataProfile) -> RegistryValidationResult:
        if not isinstance(profile, RegistryMetadataProfile):
            raise TypeError("profile must be a RegistryMetadataProfile.")

        collector = RegistryValidationCollector()

        def add(
            severity: ValidationSeverity,
            code: str,
            field: str,
            message: str,
            suggestion: str | None = None,
        ) -> None:
            collector.add(
                RegistryValidationMessage(
                    severity=severity,
                    code=code,
                    field=field,
                    message=message,
                    suggestion=suggestion,
                )
            )

        capabilities = profile.capabilities
        classification = profile.data_classification
        training = profile.training_eligibility
        provenance = profile.provenance
        retention = profile.retention

        # 1. Capability completeness and runtime observations.
        if not capabilities:
            add(
                ValidationSeverity.WARNING,
                "REGISTRY_METADATA_NO_CAPABILITIES_DECLARED",
                "capabilities",
                "The metadata profile declares no registry capabilities.",
                "Declare at least one supported capability before operational activation, or keep the registry explicitly reserved.",
            )
        elif not any(cap.supported for cap in capabilities):
            add(
                ValidationSeverity.WARNING,
                "REGISTRY_METADATA_NO_SUPPORTED_CAPABILITIES",
                "capabilities",
                "The metadata profile contains capabilities, but none are currently supported.",
                "Mark an implemented capability as supported before operational activation.",
            )

        if capabilities and not any(
            cap.simulation_supported or cap.production_supported
            for cap in capabilities
            if cap.supported
        ):
            add(
                ValidationSeverity.WARNING,
                "REGISTRY_METADATA_NO_RUNTIME_CAPABILITY",
                "capabilities",
                "No supported capability is enabled for simulation or production runtime use.",
                "Enable an appropriate runtime only after the capability implementation is ready.",
            )

        has_simulation_capability = any(
            cap.supported
            and cap.simulation_supported
            and cap.category is RegistryCapabilityCategory.SIMULATION
            for cap in capabilities
        )
        has_production_capability = any(
            cap.supported and cap.production_supported for cap in capabilities
        )

        # 2. Classification and training compatibility.
        if (
            classification.level >= RegistryClassificationLevel.CONFIDENTIAL
            and training.status is RegistryTrainingEligibilityStatus.ELIGIBLE
        ):
            add(
                ValidationSeverity.ERROR,
                "REGISTRY_METADATA_TRAINING_CLASSIFICATION_CONFLICT",
                "training_eligibility.status",
                "Confidential or stronger registry data cannot be unconditionally training eligible.",
                "Use conditional eligibility with approved safeguards, or mark the data ineligible or prohibited.",
            )

        if (
            classification.contains_sensitive_personal_data
            and training.status
            is RegistryTrainingEligibilityStatus.CONDITIONALLY_ELIGIBLE
            and not (
                training.anonymisation_required
                or training.aggregation_required
            )
        ):
            add(
                ValidationSeverity.ERROR,
                "REGISTRY_METADATA_SENSITIVE_TRAINING_CONDITION_REQUIRED",
                "training_eligibility",
                "Sensitive personal data requires anonymisation or aggregation before conditional eligibility.",
                "Require anonymisation or aggregation, or make the registry ineligible for training.",
            )
        elif (
            classification.contains_personal_data
            and training.status
            is RegistryTrainingEligibilityStatus.CONDITIONALLY_ELIGIBLE
            and not (
                training.anonymisation_required
                or training.aggregation_required
                or training.human_approval_required
                or training.consent_required
            )
        ):
            add(
                ValidationSeverity.WARNING,
                "REGISTRY_METADATA_PERSONAL_TRAINING_REVIEW_REQUIRED",
                "training_eligibility",
                "Personal data is conditionally eligible without anonymisation, aggregation, consent, or human approval safeguards.",
                "Add an appropriate safeguard or obtain policy review before training use.",
            )

        # 3. Provenance and training compatibility.
        if (
            training.status is RegistryTrainingEligibilityStatus.ELIGIBLE
            and provenance.source_type is RegistryProvenanceSourceType.UNKNOWN
            and not provenance.verified
        ):
            add(
                ValidationSeverity.ERROR,
                "REGISTRY_METADATA_UNKNOWN_PROVENANCE_TRAINING_CONFLICT",
                "provenance.source_type",
                "Unknown and unverified provenance cannot support unconditional training eligibility.",
                "Provide verified source provenance or reduce training eligibility.",
            )
        elif (
            training.status
            is RegistryTrainingEligibilityStatus.CONDITIONALLY_ELIGIBLE
            and not provenance.verified
        ):
            add(
                ValidationSeverity.WARNING,
                "REGISTRY_METADATA_UNVERIFIED_PROVENANCE_TRAINING_REVIEW",
                "provenance.verified",
                "Conditionally eligible training data has not been provenance-verified.",
                "Verify the source or require explicit human review before any training use.",
            )

        if (
            provenance.source_type
            is RegistryProvenanceSourceType.SIMULATION_GENERATOR
            and not has_simulation_capability
        ):
            add(
                ValidationSeverity.ERROR,
                "REGISTRY_METADATA_GENERATED_WITHOUT_SIMULATION_CAPABILITY",
                "capabilities",
                "Simulation-generator provenance requires at least one supported simulation capability.",
                "Declare an appropriate simulation capability or correct the provenance source type.",
            )

        if (
            has_production_capability
            and provenance.source_type is RegistryProvenanceSourceType.UNKNOWN
            and not provenance.verified
        ):
            add(
                ValidationSeverity.WARNING,
                "REGISTRY_METADATA_PRODUCTION_UNKNOWN_PROVENANCE",
                "provenance",
                "The profile supports production operations but its source provenance is unknown and unverified.",
                "Verify the provenance before production activation or require explicit governance review.",
            )

        # 4. Retention compatibility and traceability.
        if (
            retention.mode is RegistryRetentionMode.PERMANENT
            and retention.deletion_permitted
        ):
            add(
                ValidationSeverity.ERROR,
                "REGISTRY_METADATA_RETENTION_CONFLICT",
                "retention.deletion_permitted",
                "Permanent retention cannot permit deletion.",
                "Disable deletion permission or choose a non-permanent retention policy.",
            )

        if (
            classification.level is RegistryClassificationLevel.HIGHLY_RESTRICTED
            and retention.mode is RegistryRetentionMode.PERMANENT
            and not retention.policy_reference
        ):
            add(
                ValidationSeverity.WARNING,
                "REGISTRY_METADATA_SENSITIVE_PERMANENT_RETENTION_POLICY_MISSING",
                "retention.policy_reference",
                "Permanent retention of highly restricted data has no governing policy reference.",
                "Reference the approved policy that requires permanent preservation.",
            )

        # 5. Governance review observations.
        if profile.review_status == "unreviewed" and has_production_capability:
            add(
                ValidationSeverity.WARNING,
                "REGISTRY_METADATA_PRODUCTION_PROFILE_UNREVIEWED",
                "review_status",
                "A production-capable metadata profile has not been reviewed.",
                "Complete metadata governance review before production activation.",
            )
        elif profile.review_status == "rejected":
            add(
                ValidationSeverity.INFORMATION,
                "REGISTRY_METADATA_PROFILE_REJECTED",
                "review_status",
                "The metadata profile is structurally evaluable but has a rejected governance status.",
                "Do not activate the profile unless a new reviewed version is approved.",
            )

        if has_production_capability and training.simulation_only:
            add(
                ValidationSeverity.INFORMATION,
                "REGISTRY_METADATA_PRODUCTION_CAPABILITY_SIMULATION_TRAINING",
                "training_eligibility.simulation_only",
                "The registry supports production operations while training eligibility is restricted to simulation data.",
                "Preserve the simulation-only training boundary unless governance explicitly changes it.",
            )

        return collector.build(
            metadata={
                "validator": "registry_metadata",
                "validator_version": cls.VERSION,
                "registry_id": profile.registry_id,
                "profile_version": profile.profile_version,
                "review_status": profile.review_status,
            }
        )

    @classmethod
    def validate_or_raise(
        cls,
        profile: RegistryMetadataProfile,
    ) -> RegistryValidationResult:
        """Return a valid result or raise InvalidRegistryMetadataError."""
        result = cls.validate(profile)
        if result.invalid:
            raise InvalidRegistryMetadataError(result)
        return result


__all__ = ["RegistryMetadataValidator"]
