"""Environment-aware rollback planning and execution boundaries."""
from __future__ import annotations
from dataclasses import dataclass
from .errors import MigrationRollbackError

@dataclass(frozen=True, slots=True)
class RollbackPlan:
    migration_ids: tuple[str, ...]

class MigrationRollbackService:
    def __init__(self, adapter, migration_root): self.adapter=adapter; self.migration_root=migration_root
    def plan(self, plan, history, target_migration_id):
        applied={r.migration_id for r in history if r.status=='APPLIED'}
        ordered=[d for d in plan.rollback_order if d.identity.migration_id in applied]
        ids=[d.identity.migration_id for d in ordered]
        if target_migration_id not in ids: raise MigrationRollbackError('Target migration is not applied.')
        index=ids.index(target_migration_id)
        return RollbackPlan(tuple(ids[:index+1]))
    def execute(self, definition, *, environment_name, confirmed=False):
        if environment_name=='production': raise MigrationRollbackError('Production rollback is disabled; use a forward maintenance migration.')
        if environment_name!='development': raise MigrationRollbackError('Rollback is restricted to development by default.')
        if not confirmed: raise MigrationRollbackError('Rollback requires explicit confirmation.')
        sql=(self.migration_root/definition.rollback.relative_path).read_text(encoding='utf-8')
        self.adapter.execute_migration(sql,definition.rollback.transaction_policy)
