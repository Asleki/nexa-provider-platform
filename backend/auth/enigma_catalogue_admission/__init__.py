"""P006.UI.10.2.B — Governed Enigma catalogue admission package."""
from .contracts import (
    EnigmaCatalogueAdmissionError,
    EnigmaDatabaseQualificationError,
    EnigmaSourceQualificationError,
    QualifiedEnigmaRow,
    QualifiedEnigmaSource,
)
from .postgresql import PostgreSQLEnigmaCatalogueAdmission, validate_catalogue_transition
from .service import GovernedEnigmaCatalogueService
from .source import DEFAULT_SOURCE_SPECS, qualify_all_sources, qualify_source_bytes

__all__ = [
    "DEFAULT_SOURCE_SPECS",
    "EnigmaCatalogueAdmissionError",
    "EnigmaDatabaseQualificationError",
    "EnigmaSourceQualificationError",
    "GovernedEnigmaCatalogueService",
    "PostgreSQLEnigmaCatalogueAdmission",
    "QualifiedEnigmaRow",
    "QualifiedEnigmaSource",
    "qualify_all_sources",
    "qualify_source_bytes",
    "validate_catalogue_transition",
]
