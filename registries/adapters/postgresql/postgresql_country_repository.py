"""PostgreSQL DB-API adapter for P006.7.1.7 CountryRepository.

The adapter assumes a future governed migration creates reference.country_registry.
Bundle 13C does not mutate the locked migration manifest because its prior tests
freeze the existing six-migration chain. Credentials remain external.
"""
from __future__ import annotations
from datetime import date
from registries.country.contracts import CountryIdentity,SovereigntyStatus,CountryLifecycleStatus
from registries.country.persistence import CountryRepository,CountryRegistryRecord,CountryAlreadyExistsError,CountryNotFoundError,CountryVersionConflictError,CountryRepositoryError
from .postgresql_connection_provider import PostgreSQLConnectionProvider

COUNTRY_REGISTRY_TABLE="reference.country_registry"
COUNTRY_REGISTRY_REQUIRED_COLUMNS=("country_id","official_name","short_name","sovereignty_status","lifecycle_status","effective_from","effective_to","record_version","source_reference","alpha2_code","alpha3_code","boundary_id","boundary_version","realm_id","timezone_code","calendar_code","date_time_policy_id","currency_code","currency_symbol","persisted_at")

class PostgreSQLCountryRepository(CountryRepository):
    _SELECT=",".join(COUNTRY_REGISTRY_REQUIRED_COLUMNS)
    def __init__(self,provider):
        if not isinstance(provider,PostgreSQLConnectionProvider): raise TypeError("provider must be PostgreSQLConnectionProvider.")
        self._provider=provider
    def _run(self,fn):
        conn=self._provider.connect()
        try:r=fn(conn); conn.commit(); return r
        except (CountryAlreadyExistsError,CountryNotFoundError,CountryVersionConflictError):
            conn.rollback(); raise
        except Exception as exc:
            conn.rollback(); raise CountryRepositoryError("PostgreSQL country repository operation failed.") from exc
        finally:
            close=getattr(conn,"close",None)
            if callable(close): close()
    @staticmethod
    def _params(r):
        i=r.identity
        return (r.country_id,i.official_name,i.short_name,i.sovereignty_status.value,i.status.value,i.effective_from,i.effective_to,i.record_version,i.source_reference,r.alpha2_code,r.alpha3_code,r.boundary_id,r.boundary_version,r.realm_id,r.timezone_code,r.calendar_code,r.date_time_policy_id,r.currency_code,r.currency_symbol,r.persisted_at)
    @staticmethod
    def _row(row):
        d=dict(row) if hasattr(row,"keys") else dict(zip(COUNTRY_REGISTRY_REQUIRED_COLUMNS,row,strict=True))
        identity=CountryIdentity(d["country_id"],d["official_name"],d["short_name"],SovereigntyStatus(d["sovereignty_status"]),CountryLifecycleStatus(d["lifecycle_status"]),d["effective_from"],d["effective_to"],int(d["record_version"]),d["source_reference"] or "")
        return CountryRegistryRecord(identity,d["alpha2_code"],d["alpha3_code"],d["boundary_id"],int(d["boundary_version"]),d["realm_id"],d["timezone_code"],d["calendar_code"],d["date_time_policy_id"],d["currency_code"],d["currency_symbol"],d["persisted_at"])
    def add(self,r):
        if not isinstance(r,CountryRegistryRecord): raise TypeError("record must be CountryRegistryRecord.")
        def op(c):
            cur=c.cursor(); cur.execute(f"SELECT 1 FROM {COUNTRY_REGISTRY_TABLE} WHERE country_id=%s",(r.country_id,))
            if cur.fetchone() is not None: raise CountryAlreadyExistsError(r.country_id)
            placeholders=",".join(["%s"]*len(COUNTRY_REGISTRY_REQUIRED_COLUMNS)); cur.execute(f"INSERT INTO {COUNTRY_REGISTRY_TABLE} ({self._SELECT}) VALUES ({placeholders})",self._params(r)); return r
        return self._run(op)
    def get(self,country_id):
        key=str(country_id).strip().lower()
        def op(c):
            cur=c.cursor(); cur.execute(f"SELECT {self._SELECT} FROM {COUNTRY_REGISTRY_TABLE} WHERE country_id=%s",(key,)); row=cur.fetchone()
            if row is None: raise CountryNotFoundError(key)
            return self._row(row)
        return self._run(op)
    def replace(self,r,*,expected_version):
        if r.record_version!=expected_version+1: raise CountryVersionConflictError("replacement record_version must increment by exactly one.")
        def op(c):
            cur=c.cursor(); cur.execute(f"SELECT record_version FROM {COUNTRY_REGISTRY_TABLE} WHERE country_id=%s FOR UPDATE",(r.country_id,)); row=cur.fetchone()
            if row is None: raise CountryNotFoundError(r.country_id)
            if int(row[0])!=expected_version: raise CountryVersionConflictError("stored country version changed.")
            assignments=",".join(f"{x}=%s" for x in COUNTRY_REGISTRY_REQUIRED_COLUMNS[1:]); cur.execute(f"UPDATE {COUNTRY_REGISTRY_TABLE} SET {assignments} WHERE country_id=%s",self._params(r)[1:]+(r.country_id,)); return r
        return self._run(op)
    def exists(self,country_id):
        key=str(country_id).strip().lower(); return self._run(lambda c:(lambda cur:(cur.execute(f"SELECT 1 FROM {COUNTRY_REGISTRY_TABLE} WHERE country_id=%s",(key,)),cur.fetchone() is not None)[1])(c.cursor()))
    def list_all(self):
        return self._run(lambda c:(lambda cur:(cur.execute(f"SELECT {self._SELECT} FROM {COUNTRY_REGISTRY_TABLE} ORDER BY country_id"),tuple(self._row(x) for x in cur.fetchall()))[1])(c.cursor()))

__all__=["COUNTRY_REGISTRY_TABLE","COUNTRY_REGISTRY_REQUIRED_COLUMNS","PostgreSQLCountryRepository"]
