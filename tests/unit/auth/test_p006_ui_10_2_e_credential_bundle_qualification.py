from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path

import pytest

from backend.auth.admin_review_persistence.qualification import (
    B_CATALOGUES, REQUIRED_C_COLUMNS, REQUIRED_C_CONSTRAINTS,
    REQUIRED_C_FUNCTIONS, REQUIRED_C_INDEXES, REQUIRED_C_TRIGGERS,
)
from backend.auth.email_verification_persistence.qualification import (
    D_MIGRATION_ID, D_SEQUENCE, POST_D_AUTH_TABLES,
    REQUIRED_D_COLUMNS, REQUIRED_D_CONSTRAINTS, REQUIRED_D_FUNCTIONS,
    REQUIRED_D_INDEXES, REQUIRED_D_TRIGGERS,
)
from backend.auth.credential_bundle_persistence.contracts import CredentialBundleQualificationError
from backend.auth.credential_bundle_persistence.qualification import (
    E_CATALOGUE_VERSION, E_FORWARD_FILE, E_MIGRATION_ID, E_ROLLBACK_FILE, E_SEQUENCE,
    POST_E_AUTH_TABLES, REQUIRED_E_COLUMNS, REQUIRED_E_CONSTRAINTS,
    REQUIRED_E_FUNCTIONS, REQUIRED_E_INDEXES, REQUIRED_E_TRIGGERS,
    PostgreSQLCredentialBundleQualification,
)


def _root() -> Path:
    return Path(__file__).resolve().parents[3]


def _rows(root: Path | None = None) -> list[dict[str, object]]:
    root = root or _root()
    return json.loads((root / "database/migrations/migration_manifest.json").read_text())['migrations']


def _ledger(rows: list[dict[str, object]], count: int) -> list[tuple[object, ...]]:
    return [(r['migration_id'], r['sequence_number'], r['forward_sha256'], 'APPLIED') for r in rows[:count]]


class Cursor:
    def __init__(self, *, ledger_rows, tables, missing=None, operational_count=0,
                 bundle_count=0, database='npp_dev', tls=True):
        self.ledger_rows=list(ledger_rows); self.tables=tuple(tables); self.missing=missing
        self.operational_count=operational_count; self.bundle_count=bundle_count
        self.database=database; self.tls=tls; self._result=[]
    def __enter__(self): return self
    def __exit__(self,*args): return False
    def execute(self, sql, params=None):
        s=' '.join(str(sql).split())
        if s == 'SELECT current_database()': self._result=[(self.database,)]
        elif 'FROM pg_stat_ssl' in s: self._result=[(self.tls,)]
        elif 'FROM platform.schema_migration' in s: self._result=list(self.ledger_rows)
        elif 'FROM information_schema.tables' in s: self._result=[(x,) for x in self.tables]
        elif 'FROM information_schema.columns' in s:
            table=str(params[0])
            if table in REQUIRED_C_COLUMNS: values=set(REQUIRED_C_COLUMNS[table])
            elif table == 'email_verification_challenge': values=set(REQUIRED_D_COLUMNS)
            else: values=set(dict(REQUIRED_E_COLUMNS)[table])
            if self.missing in values: values.remove(self.missing)
            self._result=[(x,) for x in values]
        elif 'FROM pg_indexes' in s:
            values=set(REQUIRED_C_INDEXES | REQUIRED_D_INDEXES | REQUIRED_E_INDEXES)
            if self.missing in values: values.remove(self.missing)
            self._result=[(x,) for x in values]
        elif 'FROM information_schema.table_constraints' in s:
            values=set(REQUIRED_C_CONSTRAINTS | REQUIRED_D_CONSTRAINTS | REQUIRED_E_CONSTRAINTS)
            if self.missing in values: values.remove(self.missing)
            self._result=[(x,) for x in values]
        elif 'FROM information_schema.routines' in s:
            values=set(REQUIRED_C_FUNCTIONS | REQUIRED_D_FUNCTIONS | REQUIRED_E_FUNCTIONS)
            if self.missing in values: values.remove(self.missing)
            self._result=[(x,) for x in values]
        elif 'FROM information_schema.triggers' in s:
            values=set(REQUIRED_C_TRIGGERS | REQUIRED_D_TRIGGERS | REQUIRED_E_TRIGGERS)
            if self.missing in values: values.remove(self.missing)
            self._result=[(x,) for x in values]
        elif 'CROSS JOIN LATERAL aclexplode' in s: self._result=[(0,)]
        elif 'FROM information_schema.table_privileges' in s: self._result=[(0,)]
        elif 'FROM information_schema.routine_privileges' in s: self._result=[(0,)]
        elif 'FROM nexilabs_auth.enigma_catalogue' in s and 'COUNT' not in s: self._result=list(B_CATALOGUES)
        elif 'FROM nexilabs_auth.enigma_catalogue_entry' in s and 'GROUP BY' in s: self._result=[(3,93),(4,93),(5,93)]
        elif s.startswith('SELECT COUNT(*) FROM nexilabs_auth.'):
            table=s.split('FROM nexilabs_auth.',1)[1].split()[0]
            value=self.bundle_count if table in {'credential_bundle','credential_bundle_secret','credential_delivery'} else self.operational_count
            self._result=[(value,)]
        else: raise AssertionError(f'unexpected SQL: {s}')
    def fetchone(self): return self._result[0]
    def fetchall(self): return list(self._result)


class Connection:
    def __init__(self,cursor): self._cursor=cursor
    def cursor(self): return self._cursor


class Pool:
    def __init__(self,cursor): self.cursor_obj=cursor; self.read_only=[]
    @contextmanager
    def connection(self,read_only=False): self.read_only.append(read_only); yield Connection(self.cursor_obj)


def _successor_root(tmp_path: Path) -> tuple[Path, list[dict[str, object]]]:
    src=_root(); root=tmp_path/'repo'; d=root/'database/migrations'; d.mkdir(parents=True)
    for name in (E_FORWARD_FILE,E_ROLLBACK_FILE,'migration_manifest.json'):
        (d/name).write_bytes((src/'database/migrations'/name).read_bytes())
    p=d/'migration_manifest.json'; payload=json.loads(p.read_text()); payload['catalogue_version']=max(int(payload['catalogue_version']), E_CATALOGUE_VERSION)+1
    next_sequence=len(payload['migrations'])+1
    dependency=str(payload['migrations'][-1]['migration_id'])
    payload['migrations'].append({
        'migration_id':'m006_10_02_later_successor','milestone_id':'M006.10.2','sequence_number':next_sequence,
        'description':'later_successor','forward_file':'m006_10_02_later_successor.sql',
        'rollback_file':'m006_10_02_later_successor_rollback.sql','forward_sha256':'a'*64,
        'rollback_sha256':'b'*64,'forward_byte_size':1,'rollback_byte_size':1,
        'depends_on':[dependency],'transaction_policy':'embedded',
        'expected_objects':{'schemas':[],'tables':[],'indexes':[],'constraints':[],'views':[],'functions':[]},
        'destructive':False,'catalogue_entry_version':1})
    p.write_text(json.dumps(payload,indent=2)+'\n')
    return root,payload['migrations']


def test_repository_artifact_gate_locks_exact_e_row_34_hashes_and_d_predecessor() -> None:
    result=PostgreSQLCredentialBundleQualification.verify_repository_artifacts(_root())
    assert len(result)>=E_SEQUENCE
    assert result[32]['migration_id']==D_MIGRATION_ID
    assert result[33]['migration_id']==E_MIGRATION_ID
    assert result[33]['sequence_number']==E_SEQUENCE
    assert result[33]['depends_on']==[D_MIGRATION_ID]


def test_repository_artifact_gate_is_successor_safe(tmp_path: Path) -> None:
    root,_=_successor_root(tmp_path)
    result=PostgreSQLCredentialBundleQualification.verify_repository_artifacts(root)
    assert len(result)>E_SEQUENCE and result[E_SEQUENCE-1]['migration_id']==E_MIGRATION_ID


def test_preflight_proves_exact_d_database_predecessor_and_zero_operational_authority() -> None:
    rows=_rows(); pool=Pool(Cursor(ledger_rows=_ledger(rows,D_SEQUENCE),tables=POST_D_AUTH_TABLES))
    result=PostgreSQLCredentialBundleQualification(pool).preflight(repository_root=_root())
    assert result.phase=='pre-E'
    assert result.database_migration_count==33
    assert result.migration_tail_id==D_MIGRATION_ID
    assert result.bundle_count==result.bundle_secret_count==result.delivery_count==0
    assert pool.read_only==[True]


def test_preflight_rejects_non_d_database_tail() -> None:
    rows=_rows(); cursor=Cursor(ledger_rows=_ledger(rows,E_SEQUENCE),tables=POST_E_AUTH_TABLES)
    with pytest.raises(CredentialBundleQualificationError,match='expected 33'):
        PostgreSQLCredentialBundleQualification(Pool(cursor)).preflight(repository_root=_root())


def test_post_e_verify_proves_structure_acl_catalogues_and_zero_closure() -> None:
    rows=_rows(); pool=Pool(Cursor(ledger_rows=_ledger(rows,E_SEQUENCE),tables=POST_E_AUTH_TABLES))
    result=PostgreSQLCredentialBundleQualification(pool).verify(repository_root=_root())
    assert result.phase=='post-E'
    assert result.database_migration_count==34
    assert result.nexilabs_auth_tables==POST_E_AUTH_TABLES
    assert result.enigma_catalogue_count==3 and result.enigma_catalogue_entry_count==279
    assert result.public_schema_privilege_count==result.public_table_privilege_count==result.public_routine_privilege_count==0
    assert result.bundle_count==result.bundle_secret_count==result.delivery_count==0


def test_post_e_tail_rejects_any_seeded_operational_authority() -> None:
    rows=_rows(); cursor=Cursor(ledger_rows=_ledger(rows,E_SEQUENCE),tables=POST_E_AUTH_TABLES,bundle_count=1)
    with pytest.raises(CredentialBundleQualificationError,match='zero operational authority rows'):
        PostgreSQLCredentialBundleQualification(Pool(cursor)).verify(repository_root=_root())


def test_successor_era_does_not_falsely_reject_later_operational_data(tmp_path: Path) -> None:
    root,rows=_successor_root(tmp_path)
    tables=tuple(sorted((*POST_E_AUTH_TABLES,'later_successor_table')))
    cursor=Cursor(ledger_rows=_ledger(rows,len(rows)),tables=tables,operational_count=2,bundle_count=3)
    result=PostgreSQLCredentialBundleQualification(Pool(cursor)).verify(repository_root=root)
    assert result.database_migration_count==len(rows) and result.bundle_count==3 and result.principal_count==2


def test_missing_d_or_e_structure_fails_closed() -> None:
    rows=_rows()
    for missing,label in (
        (next(iter(REQUIRED_C_TRIGGERS)),'C'),
        (next(iter(REQUIRED_D_TRIGGERS)),'D'),
        (next(iter(REQUIRED_E_CONSTRAINTS)),'E'),
    ):
        cursor=Cursor(ledger_rows=_ledger(rows,E_SEQUENCE),tables=POST_E_AUTH_TABLES,missing=missing)
        with pytest.raises(CredentialBundleQualificationError,match=f'missing {label}'):
            PostgreSQLCredentialBundleQualification(Pool(cursor)).verify(repository_root=_root())


def test_wrong_database_and_missing_tls_fail_closed() -> None:
    rows=_rows()
    with pytest.raises(CredentialBundleQualificationError,match='wrong database target'):
        PostgreSQLCredentialBundleQualification(Pool(Cursor(ledger_rows=_ledger(rows,D_SEQUENCE),tables=POST_D_AUTH_TABLES,database='wrong'))).preflight(repository_root=_root())
    with pytest.raises(CredentialBundleQualificationError,match='TLS is not active'):
        PostgreSQLCredentialBundleQualification(Pool(Cursor(ledger_rows=_ledger(rows,D_SEQUENCE),tables=POST_D_AUTH_TABLES,tls=False))).preflight(repository_root=_root())
