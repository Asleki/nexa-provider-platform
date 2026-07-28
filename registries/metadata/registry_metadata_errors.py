"""Registry metadata contract errors."""

class RegistryMetadataError(ValueError):
    """Base error raised by registry metadata contracts."""

class RegistryCapabilityError(RegistryMetadataError):
    """Raised for invalid registry capability declarations."""

class RegistryClassificationError(RegistryMetadataError):
    """Raised for invalid data classification declarations."""

class RegistryTrainingEligibilityError(RegistryMetadataError):
    """Raised for invalid training eligibility declarations."""

class RegistryProvenanceError(RegistryMetadataError):
    """Raised for invalid provenance declarations."""

class RegistryRetentionError(RegistryMetadataError):
    """Raised for invalid retention declarations."""

class RegistryMetadataProfileError(RegistryMetadataError):
    """Raised for invalid aggregate registry metadata profiles."""

__all__ = [
    "RegistryMetadataError", "RegistryCapabilityError", "RegistryClassificationError",
    "RegistryTrainingEligibilityError", "RegistryProvenanceError", "RegistryRetentionError",
    "RegistryMetadataProfileError",
]
