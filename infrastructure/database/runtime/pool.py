from contextlib import contextmanager
from contextvars import ContextVar

from .read_materialization import RequestReadMaterialization


class DatabaseUnavailable(RuntimeError):
    pass


class PostgreSQLPool:
    def __init__(self, settings, pool_factory=None):
        self.settings = settings
        self._factory = pool_factory
        self._pool = None
        self._active_read_connection = ContextVar(
            f"postgresql_pool_read_connection_{id(self)}",
            default=None,
        )
        self._active_read_materialization = ContextVar(
            f"postgresql_pool_read_materialization_{id(self)}",
            default=None,
        )

    @property
    def is_open(self):
        return self._pool is not None

    def open(self):
        if self._pool is not None:
            return
        try:
            if self._factory:
                self._pool = self._factory(self.settings)
            else:
                from psycopg_pool import ConnectionPool

                conninfo = (
                    f"host={self.settings.host} port={self.settings.port} "
                    f"dbname={self.settings.database_name} user={self.settings.username} "
                    f"password={self.settings.password} sslmode={self.settings.ssl_mode}"
                )
                self._pool = ConnectionPool(
                    conninfo=conninfo,
                    min_size=self.settings.min_pool_size,
                    max_size=self.settings.max_pool_size,
                    timeout=self.settings.acquisition_timeout_seconds,
                    check=ConnectionPool.check_connection,
                    open=True,
                )
        except Exception as exc:
            raise DatabaseUnavailable("database pool could not be opened") from exc

    def close(self):
        if self._pool is not None:
            self._pool.close()
            self._pool = None

    def readiness(self):
        try:
            with self.connection(read_only=True) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    row = cur.fetchone()
            return row == (1,)
        except Exception:
            return False

    def current_read_materialization(self):
        return self._active_read_materialization.get()

    @contextmanager
    def read_session(self):
        """Acquire one checked read-only connection for a logical request.

        Repository methods keep using ``connection(read_only=True)`` unchanged;
        nested calls in this context reuse the same connection. ContextVar keeps
        the lease request/task-local and prevents cross-request connection leaks.
        """
        if self._pool is None:
            raise DatabaseUnavailable("database pool is not open")

        active = self._active_read_connection.get()
        if active is not None:
            yield active
            return

        try:
            with self._pool.connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SET TRANSACTION READ ONLY")
                connection_token = self._active_read_connection.set(conn)
                materialization_token = self._active_read_materialization.set(
                    RequestReadMaterialization()
                )
                try:
                    yield conn
                finally:
                    self._active_read_materialization.reset(materialization_token)
                    self._active_read_connection.reset(connection_token)
        except DatabaseUnavailable:
            raise
        except Exception as exc:
            raise DatabaseUnavailable("database operation failed") from exc

    @contextmanager
    def connection(self, read_only=False):
        if self._pool is None:
            raise DatabaseUnavailable("database pool is not open")

        if read_only:
            active = self._active_read_connection.get()
            if active is not None:
                yield active
                return

        try:
            with self._pool.connection() as conn:
                if read_only:
                    with conn.cursor() as cur:
                        cur.execute("SET TRANSACTION READ ONLY")
                yield conn
        except DatabaseUnavailable:
            raise
        except Exception as exc:
            raise DatabaseUnavailable("database operation failed") from exc
