"""Runtime handler adapter for governed administrative-boundary legalization."""
from __future__ import annotations
from .execution import execute_administrative_boundary_legalization
def legalize_administrative_boundaries_handler(repository,command):
    return execute_administrative_boundary_legalization(repository,command['submitter_actor_id'],command['approver_actor_id'],command.get('repository_revision','bundle19-working-tree'))
