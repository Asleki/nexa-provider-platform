"""Errors for M009.13.10 reference-registry qualification."""


class ReferenceQualificationError(RuntimeError):
    """Base failure for repeatable reference qualification operations."""


class SchemaInspectionError(ReferenceQualificationError):
    """Raised when PostgreSQL structural inspection cannot complete."""


class ProductionAuthoringQualificationError(ReferenceQualificationError):
    """Raised when production authoring violates the qualification contract."""


__all__ = [
    "ReferenceQualificationError",
    "SchemaInspectionError",
    "ProductionAuthoringQualificationError",
]
