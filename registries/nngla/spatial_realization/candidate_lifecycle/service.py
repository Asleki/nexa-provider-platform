"""High-level governed candidate lifecycle facade for Delivery 2."""
from __future__ import annotations

from .governance import bind_governance_decisions
from .package import build_candidate_package, candidate_run_identity
from .qualification import qualify_package


class GovernedCandidateLifecycleService:
    def __init__(self, repository) -> None:
        self.repository = repository

    def record_preview(self, preview, *, runtime_mode, author_actor_id, face_decisions=(), boundary_decisions=(), reviewer_actor_id="", approver_actor_id="", parent_candidate_id="", parent_candidate_geometry_sha256=""):
        decisions = ()
        if face_decisions or boundary_decisions:
            run_id, _ = candidate_run_identity(
                preview,
                runtime_mode=runtime_mode,
                parent_candidate_id=parent_candidate_id,
                parent_candidate_geometry_sha256=parent_candidate_geometry_sha256,
            )
            decisions = bind_governance_decisions(
                fabric_run_id=run_id,
                scope_fingerprint=preview.scope.fingerprint,
                face_decisions=tuple(face_decisions), boundary_decisions=tuple(boundary_decisions),
                reviewer_actor_id=reviewer_actor_id, approver_actor_id=approver_actor_id,
                runtime_mode=runtime_mode,
            )
        package = build_candidate_package(
            preview, runtime_mode=runtime_mode, author_actor_id=author_actor_id, decisions=decisions,
            parent_candidate_id=parent_candidate_id,
            parent_candidate_geometry_sha256=parent_candidate_geometry_sha256,
        )
        return self.repository.persist(package)

    def qualify(self, package, preview, *, qualifier_actor_id, connection=None, qualified_parent_candidate_id="", qualified_parent_candidate_geometry_sha256="", geometry_overrides=None):
        decision = qualify_package(
            package, preview,
            qualifier_actor_id=qualifier_actor_id,
            connection=connection,
            qualified_parent_candidate_id=qualified_parent_candidate_id,
            qualified_parent_candidate_geometry_sha256=qualified_parent_candidate_geometry_sha256,
            geometry_overrides=geometry_overrides,
        )
        persist = getattr(self.repository, "persist_qualification", None)
        return persist(decision) if persist is not None else decision


__all__ = ["GovernedCandidateLifecycleService"]
