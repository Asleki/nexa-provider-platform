"""Stable errors for repository-side database migration control."""

class MigrationControlError(Exception):
    """Base error for migration-control validation failures."""

    code = "MIGRATION_CONTROL_ERROR"

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class MigrationManifestError(MigrationControlError):
    code = "MIGRATION_MANIFEST_INVALID"


class MigrationIdentityError(MigrationControlError):
    code = "MIGRATION_IDENTITY_INVALID"


class MigrationDiscoveryError(MigrationControlError):
    code = "MIGRATION_DISCOVERY_FAILED"


class MigrationPathError(MigrationControlError):
    code = "MIGRATION_PATH_UNSAFE"


class MigrationDuplicateError(MigrationControlError):
    code = "MIGRATION_DUPLICATE"


class MigrationPairingError(MigrationControlError):
    code = "MIGRATION_PAIRING_INVALID"


class MigrationDependencyError(MigrationControlError):
    code = "MIGRATION_DEPENDENCY_INVALID"


class MigrationCycleError(MigrationDependencyError):
    code = "MIGRATION_DEPENDENCY_CYCLE"


class MigrationOrderError(MigrationControlError):
    code = "MIGRATION_ORDER_INVALID"


class MigrationChecksumError(MigrationControlError):
    code = "MIGRATION_CHECKSUM_MISMATCH"


class MigrationPlanError(MigrationControlError):
    code = "MIGRATION_PLAN_INVALID"


__all__ = [
    "MigrationControlError",
    "MigrationManifestError",
    "MigrationIdentityError",
    "MigrationDiscoveryError",
    "MigrationPathError",
    "MigrationDuplicateError",
    "MigrationPairingError",
    "MigrationDependencyError",
    "MigrationCycleError",
    "MigrationOrderError",
    "MigrationChecksumError",
    "MigrationPlanError",
]
