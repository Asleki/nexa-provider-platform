
"""
Nexa Provider Platform
Unit Tests: Repository Registry
Milestone: NPP-M005.5
"""

import unittest

from shared.repositories.repository_registry import (
    RepositoryRegistry,
    normalize_repository_type,
)
from shared.repositories.repository_interface import RepositoryInterface
from shared.repositories.repository_errors import (
    RepositoryAlreadyRegisteredError,
    RepositoryConfigurationError,
    RepositoryNotRegisteredError,
)
from shared.repositories.repository_types import RepositoryType


class DummyRepository(RepositoryInterface):
    @property
    def repository_name(self): return "dummy"
    @property
    def repository_type(self): return "local"
    @property
    def id_field(self): return "id"
    def create(self, record): pass
    def get(self, record_id): pass
    def update(self, record_id, record): pass
    def delete(self, record_id): pass
    def list_all(self): pass
    def exists(self, record_id): pass
    def count(self): pass


class RepositoryRegistryTests(unittest.TestCase):

    def test_normalize_repository_type(self):
        self.assertEqual(normalize_repository_type(RepositoryType.LOCAL), "local")
        self.assertEqual(normalize_repository_type(" Local "), "local")
        with self.assertRaises(RepositoryConfigurationError):
            normalize_repository_type("")

    def test_register_and_get(self):
        reg = RepositoryRegistry()
        reg.register("dummy", DummyRepository)
        self.assertTrue(reg.is_registered("dummy"))
        self.assertIs(reg.get("dummy"), DummyRepository)

    def test_duplicate_registration(self):
        reg = RepositoryRegistry()
        reg.register("dummy", DummyRepository)
        with self.assertRaises(RepositoryAlreadyRegisteredError):
            reg.register("dummy", DummyRepository)

    def test_replace_registration(self):
        reg = RepositoryRegistry()
        reg.register("dummy", DummyRepository)
        reg.register("dummy", DummyRepository, replace=True)
        self.assertIs(reg.get("dummy"), DummyRepository)

    def test_unregister(self):
        reg = RepositoryRegistry()
        reg.register("dummy", DummyRepository)
        reg.unregister("dummy")
        with self.assertRaises(RepositoryNotRegisteredError):
            reg.get("dummy")

    def test_len_contains_iter_clear(self):
        reg = RepositoryRegistry()
        reg.register("dummy", DummyRepository)
        self.assertEqual(len(reg), 1)
        self.assertIn("dummy", reg)
        self.assertEqual(tuple(reg), ("dummy",))
        reg.clear()
        self.assertEqual(len(reg), 0)


if __name__ == "__main__":
    unittest.main()
