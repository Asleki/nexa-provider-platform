"""High-level reusable facade for preview, national dry assessment and execution."""
from __future__ import annotations

from .execution import execute_preview
from .preview import build_preview
from .selection import eligible_city_root_ids


class GovernedSpatialBatchEngine:
    def __init__(self, repository, topology_engine, *, repository_revision: str) -> None:
        revision=str(repository_revision).strip()
        if not revision:raise ValueError("repository_revision is required")
        self.repository=repository;self.topology_engine=topology_engine;self.repository_revision=revision

    def preview(self, root_ids):
        return build_preview(self.repository,self.topology_engine,root_ids=root_ids,repository_revision=self.repository_revision)

    def assess_all_major_cities(self):
        return self.preview(eligible_city_root_ids())

    def execute(self, root_ids, *, approved_fingerprint: str, confirmation: str, submitter_actor_id: str, approver_actor_id: str):
        return execute_preview(
            self.repository,self.topology_engine,root_ids=root_ids,repository_revision=self.repository_revision,
            approved_fingerprint=approved_fingerprint,confirmation=confirmation,
            submitter_actor_id=submitter_actor_id,approver_actor_id=approver_actor_id,
        )


__all__=["GovernedSpatialBatchEngine"]
