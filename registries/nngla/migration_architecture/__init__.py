"""P006.7.11 Bundle 16A governed migration architecture."""
from .audit import ArchitectureAuditor, ArchitectureAuditReport, AuditFinding
from .conflicts import (
    ConflictCode,
    ConflictDecision,
    ConflictDisposition,
    ConflictEvaluator,
    ConflictFinding,
    ExistingCrosswalk,
)
from .contracts import (
    CANONICAL_NAMESPACE_CONTRACTS,
    CanonicalIdentityProposal,
    CanonicalObjectFamily,
    IdentifierNamespaceContract,
    IdentifierRole,
    SourceIdentity,
)
from .identity import AllocationConflict, CanonicalIdentityAllocator, CanonicalIdentityError

__all__ = [
    "ArchitectureAuditor",
    "ArchitectureAuditReport",
    "AuditFinding",
    "ConflictCode",
    "ConflictDecision",
    "ConflictDisposition",
    "ConflictEvaluator",
    "ConflictFinding",
    "ExistingCrosswalk",
    "CANONICAL_NAMESPACE_CONTRACTS",
    "CanonicalIdentityProposal",
    "CanonicalObjectFamily",
    "IdentifierNamespaceContract",
    "IdentifierRole",
    "SourceIdentity",
    "AllocationConflict",
    "CanonicalIdentityAllocator",
    "CanonicalIdentityError",
]
