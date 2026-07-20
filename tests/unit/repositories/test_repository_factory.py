"""
Nexa Provider Platform
Unit Tests: Repository Factory
Milestone: NPP-M005.4
"""
import unittest
from unittest.mock import MagicMock

from shared.repositories.repository_factory import RepositoryFactory
from shared.repositories.repository_registry import RepositoryRegistry
from shared.repositories.repository_interface import RepositoryInterface
from shared.repositories.repository_types import RepositoryType
from shared.repositories.repository_errors import (
    RepositoryFactoryError,
    RepositoryNotRegisteredError,
)

class DummyRepository(RepositoryInterface):
    repository_name="dummy"
    repository_type="local"
    id_field="id"
    def __init__(self, **kwargs): self.kwargs=kwargs
    def create(self,r): pass
    def get(self,i): pass
    def update(self,i,r): pass
    def delete(self,i): pass
    def list_all(self): pass
    def exists(self,i): pass
    def count(self): pass

class RepositoryFactoryTests(unittest.TestCase):

    def test_registry_property(self):
        reg=RepositoryRegistry()
        fac=RepositoryFactory(reg,register_defaults=False)
        self.assertIs(fac.registry,reg)

    def test_create_registered_repository(self):
        reg=RepositoryRegistry()
        reg.register("dummy",DummyRepository)
        fac=RepositoryFactory(reg,register_defaults=False)
        repo=fac.create("dummy",repository_name="citizens")
        self.assertIsInstance(repo,DummyRepository)
        self.assertEqual(repo.kwargs["repository_name"],"citizens")

    def test_not_registered_passthrough(self):
        fac=RepositoryFactory(RepositoryRegistry(),register_defaults=False)
        with self.assertRaises(RepositoryNotRegisteredError):
            fac.create("missing")

    def test_constructor_failure_wrapped(self):
        class Broken(DummyRepository):
            def __init__(self,**kwargs):
                raise RuntimeError("boom")
        reg=RepositoryRegistry()
        reg.register("broken",Broken)
        fac=RepositoryFactory(reg,register_defaults=False)
        with self.assertRaises(RepositoryFactoryError):
            fac.create("broken",repository_name="x")

    def test_invalid_constructor_result(self):
        reg=RepositoryRegistry()
        reg.get=MagicMock(return_value=lambda **k: object())
        fac=RepositoryFactory(reg,register_defaults=False)
        with self.assertRaises(RepositoryFactoryError):
            fac.create("dummy")

    def test_register_defaults(self):
        reg=RepositoryRegistry()
        fac=RepositoryFactory(reg,register_defaults=True)
        self.assertTrue(reg.is_registered(RepositoryType.LOCAL))

if __name__=="__main__":
    unittest.main()
