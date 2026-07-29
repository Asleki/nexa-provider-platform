"""Shared builders for M008.15.7 registry metadata tests."""
from datetime import datetime, timezone

from registries.metadata import (
    RegistryCapability,
    RegistryDataClassification,
    RegistryMetadataProfile,
    RegistryProvenance,
    RegistryRetention,
    RegistryTrainingEligibility,
)

UTC_NOW = datetime(2026, 7, 29, 8, 0, tzinfo=timezone.utc)


def make_capability(**overrides):
    values = {
        "capability_id": "identity-register",
        "capability_code": "IDENTITY.REGISTER",
        "capability_name": "Register identity",
        "category": "identity",
        "simulation_supported": True,
        "production_supported": False,
    }
    values.update(overrides)
    return RegistryCapability(**values)


def make_classification(**overrides):
    values = {
        "level": "restricted",
        "reason": "Registry identity data",
        "contains_personal_data": True,
        "masking_required": True,
        "data_categories": ("IDENTITY.CORE",),
    }
    values.update(overrides)
    return RegistryDataClassification(**values)


def make_training(**overrides):
    values = {
        "status": "conditionally_eligible",
        "reason": "Controlled evaluation only",
        "anonymisation_required": True,
        "human_approval_required": True,
    }
    values.update(overrides)
    return RegistryTrainingEligibility(**values)


def make_provenance(**overrides):
    values = {
        "source_type": "institution",
        "source_system": "civil-registry",
        "source_reference": "civil.registry.ke",
        "recorded_at": UTC_NOW,
    }
    values.update(overrides)
    return RegistryProvenance(**values)


def make_retention(**overrides):
    values = {
        "mode": "permanent",
        "reason": "Legal identity history",
        "archive_required": True,
        "policy_reference": "retention.identity.v1",
    }
    values.update(overrides)
    return RegistryRetention(**values)


def make_profile(**overrides):
    values = {
        "registry_id": "citizen.registry",
        "capabilities": (make_capability(),),
        "data_classification": make_classification(),
        "training_eligibility": make_training(),
        "provenance": make_provenance(),
        "retention": make_retention(),
        "effective_from": UTC_NOW,
    }
    values.update(overrides)
    return RegistryMetadataProfile(**values)
