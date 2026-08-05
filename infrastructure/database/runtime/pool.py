from contextlib import contextmanager
class DatabaseUnavailable(RuntimeError): pass
class PostgreSQLPool:
    def __init__(self,settings,pool_factory=None): self.settings=settings; self._factory=pool_factory; self._pool=None
    @property
    def is_open(self): return self._pool is not None
    def open(self):
        if self._pool is not None:return
        try:
            if self._factory: self._pool=self._factory(self.settings)
            else:
                from psycopg_pool import ConnectionPool
                conninfo=f"host={self.settings.host} port={self.settings.port} dbname={self.settings.database_name} user={self.settings.username} password={self.settings.password} sslmode={self.settings.ssl_mode}"
                self._pool=ConnectionPool(conninfo=conninfo,min_size=self.settings.min_pool_size,max_size=self.settings.max_pool_size,timeout=self.settings.acquisition_timeout_seconds,open=True)
        except Exception as exc: raise DatabaseUnavailable("database pool could not be opened") from exc
    def close(self):
        if self._pool is not None:
            self._pool.close(); self._pool=None
    def readiness(self):
        try:
            with self.connection(read_only=True) as conn:
                with conn.cursor() as cur: cur.execute("SELECT 1"); row=cur.fetchone()
            return row==(1,)
        except Exception:return False
    @contextmanager
    def connection(self,read_only=False):
        if self._pool is None: raise DatabaseUnavailable("database pool is not open")
        try:
            with self._pool.connection() as conn:
                if read_only:
                    with conn.cursor() as cur: cur.execute("SET TRANSACTION READ ONLY")
                yield conn
        except DatabaseUnavailable: raise
        except Exception as exc: raise DatabaseUnavailable("database operation failed") from exc
