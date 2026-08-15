"""Migration-control application service."""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from .manifest import MigrationManifestLoader
from .discovery import MigrationDiscovery
from .planning import MigrationPlanner
from .errors import MigrationVerificationError, MigrationDriftError
from .contracts import MigrationDefinition

@dataclass(frozen=True,slots=True)
class MigrationStatus:
    ledger_state:str; repository_migrations:int; applied_migrations:int; pending_migrations:int
    failed_migrations:int; started_migrations:int; checksum_mismatches:int
    unknown_database_migrations:int; plan_checksum:str

@dataclass(frozen=True,slots=True)
class AppliedStructurePlan:
    forward_order:tuple[MigrationDefinition,...]

class MigrationControlService:
    def __init__(self,migration_root:Path,manifest_path:Path,ledger,bootstrap=None,lock=None,executor=None,drift_inspector=None):
        self.migration_root=Path(migration_root); self.manifest_path=Path(manifest_path); self.ledger=ledger
        self.bootstrap=bootstrap; self.lock=lock; self.executor=executor; self.drift_inspector=drift_inspector
    def trusted_plan(self):
        cat=MigrationManifestLoader().load(self.manifest_path)
        MigrationDiscovery(self.migration_root).validate_catalogue(cat)
        return MigrationPlanner().create_plan(cat)
    def status(self):
        plan=self.trusted_plan(); boot=self.ledger.is_bootstrapped(); history=self.ledger.history() if boot else ()
        by_repo={d.identity.migration_id:d for d in plan.forward_order}; applied=[r for r in history if r.status=='APPLIED']
        mismatches=sum(1 for r in history if r.migration_id in by_repo and r.checksum_sha256!=by_repo[r.migration_id].forward.sha256)
        unknown=sum(1 for r in history if r.migration_id not in by_repo)
        pending=sum(1 for d in plan.forward_order if not any(r.migration_id==d.identity.migration_id and r.status=='APPLIED' for r in history))
        return MigrationStatus('BOOTSTRAPPED' if boot else 'NOT_BOOTSTRAPPED',plan.migration_count,len(applied),pending,sum(r.status=='FAILED' for r in history),sum(r.status=='STARTED' for r in history),mismatches,unknown,plan.plan_checksum)
    def plan(self): return self.trusted_plan()
    def history(self): return self.ledger.history() if self.ledger.is_bootstrapped() else ()
    def applied_structure_plan(self):
        """Return the repository definitions whose ledger state is APPLIED.

        Structural verification is about the database state that must exist *now*.
        Repository migrations that are still pending declare future structure and must
        not be treated as drift merely because their objects do not exist yet.
        Selection is by migration identity recorded in the ledger, never by slicing
        the first N repository definitions.
        """
        plan=self.trusted_plan()
        if not self.ledger.is_bootstrapped():
            applied_ids=frozenset()
        else:
            applied_ids=frozenset(r.migration_id for r in self.ledger.history() if r.status=='APPLIED')
        forward=tuple(d for d in plan.forward_order if d.identity.migration_id in applied_ids)
        return AppliedStructurePlan(forward)
    def verify(self, *, structural=False):
        status=self.status()
        if status.checksum_mismatches or status.unknown_database_migrations or status.started_migrations:
            raise MigrationVerificationError('repository and migration ledger are inconsistent.')
        if structural and status.applied_migrations and self.drift_inspector is not None:
            report=self.drift_inspector.inspect_expected(self.applied_structure_plan())
            if not report.is_clean: raise MigrationDriftError('expected database objects are missing.')
        return status
    def apply(self,*,applied_by,database_name,environment_name,repository_revision='unknown'):
        if self.bootstrap is None or self.lock is None or self.executor is None: raise MigrationVerificationError('apply dependencies are not configured.')
        plan=self.trusted_plan(); self.bootstrap.bootstrap()
        with self.lock.acquire():
            status=self.verify()
            if status.failed_migrations: raise MigrationVerificationError('failed migration records require recovery before apply.')
            applied={r.migration_id for r in self.ledger.history() if r.status=='APPLIED'}; results=[]
            for d in plan.forward_order:
                if d.identity.migration_id not in applied:
                    results.append(self.executor.execute(d,self.ledger,applied_by=applied_by,database_name=database_name,environment_name=environment_name,repository_revision=repository_revision))
            return tuple(results)
