"""Lazy DB-API connection provider; credentials remain external."""
from __future__ import annotations
from collections.abc import Callable
class PostgreSQLConnectionProvider:
    def __init__(self,factory:Callable[[],object])->None:
        if not callable(factory): raise TypeError("factory must be callable.")
        self._factory=factory
    def connect(self)->object:
        connection=self._factory()
        if connection is None: raise RuntimeError("connection factory returned None.")
        return connection
__all__=["PostgreSQLConnectionProvider"]
