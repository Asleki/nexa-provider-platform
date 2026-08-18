from pathlib import Path
from database.migration_control.service import MigrationControlService
from database.migration_control.ledger import MemoryMigrationLedger
ROOT=Path('database/migrations')
def test_status_and_verify_are_read_only():
 l=MemoryMigrationLedger(False); s=MigrationControlService(ROOT,ROOT/'migration_manifest.json',l); assert s.status().pending_migrations==18; assert s.verify().ledger_state=='NOT_BOOTSTRAPPED'; assert not l.is_bootstrapped()


from datetime import datetime, timezone
import pytest

from database.migration_control.drift import DatabaseObjectState, MigrationDriftInspector
from database.migration_control.errors import MigrationDriftError
from database.migration_control.ledger import MigrationLedgerRecord


def _ledger_with_applied(service, count):
    ledger = service.ledger
    for definition in service.trusted_plan().forward_order[:count]:
        started = datetime.now(timezone.utc)
        ledger.insert_started(
            MigrationLedgerRecord(
                definition.identity.migration_id,
                definition.identity.milestone_id,
                definition.forward.relative_path,
                definition.identity.sequence_number,
                definition.forward.sha256,
                'STARTED',
                f'execution-{definition.identity.sequence_number}',
                started,
            )
        )
        ledger.mark_applied(
            definition.identity.migration_id,
            completed_at=started,
            duration_ms=1,
        )
    return ledger


class _RecordingDriftInspector:
    def __init__(self, clean=True):
        self.clean = clean
        self.definition_ids = ()

    def inspect_expected(self, plan):
        self.definition_ids = tuple(
            definition.identity.migration_id for definition in plan.forward_order
        )
        return type('R', (), {'is_clean': self.clean})()


def test_structural_verify_checks_only_ledger_applied_migrations_when_repository_has_pending_entries():
    ledger = MemoryMigrationLedger(True)
    drift = _RecordingDriftInspector()
    service = MigrationControlService(
        ROOT,
        ROOT / 'migration_manifest.json',
        ledger,
        drift_inspector=drift,
    )
    _ledger_with_applied(service, 6)

    status = service.verify(structural=True)

    assert status.repository_migrations == 18
    assert status.applied_migrations == 6
    assert status.pending_migrations == 12
    assert drift.definition_ids == tuple(
        definition.identity.migration_id
        for definition in service.trusted_plan().forward_order[:6]
    )


def test_applied_structure_selection_uses_ledger_identity_not_applied_count_slicing():
    ledger = MemoryMigrationLedger(True)
    service = MigrationControlService(ROOT, ROOT / 'migration_manifest.json', ledger)
    plan = service.trusted_plan()
    # Deliberately apply migration 1 and migration 3 only. The helper must not
    # infer "first two migrations" from the applied count.
    for definition in (plan.forward_order[0], plan.forward_order[2]):
        started = datetime.now(timezone.utc)
        ledger.insert_started(MigrationLedgerRecord(
            definition.identity.migration_id,
            definition.identity.milestone_id,
            definition.forward.relative_path,
            definition.identity.sequence_number,
            definition.forward.sha256,
            'STARTED',
            f'identity-{definition.identity.sequence_number}',
            started,
        ))
        ledger.mark_applied(definition.identity.migration_id, completed_at=started, duration_ms=1)

    selected = service.applied_structure_plan().forward_order
    assert [item.identity.sequence_number for item in selected] == [1, 3]


def test_structural_verify_still_detects_missing_object_from_an_applied_migration():
    ledger = MemoryMigrationLedger(True)
    service = MigrationControlService(ROOT, ROOT / 'migration_manifest.json', ledger)
    _ledger_with_applied(service, 6)
    applied = service.applied_structure_plan().forward_order

    schemas = set()
    tables = set()
    indexes = set()
    constraints = set()
    views = set()
    functions = set()
    for definition in applied:
        expected = definition.expected_objects
        schemas.update(expected.schemas)
        tables.update(expected.tables)
        indexes.update(expected.indexes)
        constraints.update(expected.constraints)
        views.update(expected.views)
        functions.update(expected.functions)

    # Migration 6 declares geography.world_boundary. Its absence must remain drift.
    tables.discard('geography.world_boundary')

    class Adapter:
        def inspect_database_objects(self):
            return DatabaseObjectState(
                schemas=frozenset(schemas),
                tables=frozenset(tables),
                indexes=frozenset(indexes),
                constraints=frozenset(constraints),
                views=frozenset(views),
                functions=frozenset(functions),
            )

    service.drift_inspector = MigrationDriftInspector(Adapter())
    with pytest.raises(MigrationDriftError, match='expected database objects are missing'):
        service.verify(structural=True)
