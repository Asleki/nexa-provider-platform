"""
============================================================
Nexa Provider Platform
File: tests/integration/repositories/test_storage_adapter_compatibility.py
Layer: Repository Integration Tests
Milestone: NPP-M005.8 — Storage Adapter Compatibility
============================================================

Verifies that LocalRepository uses the StorageManager contract
consistently across the currently available local storage adapters.

The repository remains responsible for repository behavior while
each adapter remains responsible for persistence mechanics.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from typing import Type

from shared.repositories.local_repository import LocalRepository
from shared.repositories.repository_errors import (
    RepositoryCountError,
    RepositoryStorageError,
)
from shared.repositories.repository_factory import RepositoryFactory
from shared.storage.csv_storage import CsvStorage
from shared.storage.json_storage import JsonStorage
from shared.storage.jsonl_storage import JsonlStorage
from shared.storage.storage_adapter import StorageAdapter
from shared.storage.storage_manager import StorageManager


ADAPTERS: tuple[tuple[str, Type[StorageAdapter]], ...] = (
    ("json", JsonStorage),
    ("jsonl", JsonlStorage),
    ("csv", CsvStorage),
)


class StorageAdapterCompatibilityIntegrationTests(unittest.TestCase):
    """Verify repository compatibility with registered local adapters."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage_root = Path(self.temporary_directory.name)
        self.factory = RepositoryFactory()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    @staticmethod
    def _build_manager(
        selected_backend: str,
    ) -> StorageManager:
        manager = StorageManager()

        for backend_name, adapter_type in ADAPTERS:
            manager.register_adapter(
                adapter_type(),
                make_default=(backend_name == selected_backend),
            )

        return manager

    def _build_repository(
        self,
        backend: str,
        *,
        repository_name: str = "providers",
    ) -> LocalRepository:
        manager = self._build_manager(backend)

        repository = self.factory.create_local(
            storage_manager=manager,
            repository_name=repository_name,
            id_field="provider_id",
            storage_root=self.storage_root / backend,
            backend=backend,
        )

        self.assertIsInstance(repository, LocalRepository)
        return repository

    def test_storage_manager_registers_all_supported_local_adapters(
        self,
    ) -> None:
        manager = self._build_manager("json")

        self.assertEqual(
            manager.registered_backends,
            ("csv", "json", "jsonl"),
        )
        self.assertEqual(manager.active_backend, "json")
        self.assertIsInstance(manager.get_adapter("json"), JsonStorage)
        self.assertIsInstance(manager.get_adapter("jsonl"), JsonlStorage)
        self.assertIsInstance(manager.get_adapter("csv"), CsvStorage)

    def test_complete_repository_lifecycle_works_across_adapters(
        self,
    ) -> None:
        for backend, _ in ADAPTERS:
            with self.subTest(backend=backend):
                repository = self._build_repository(backend)

                created = repository.create(
                    {
                        "provider_id": "PRV-000001",
                        "name": "Provider One",
                        "status": "pending",
                    }
                )
                self.assertTrue(created.success)
                self.assertEqual(created.record_id, "PRV-000001")

                found = repository.get("PRV-000001")
                self.assertEqual(found.record["name"], "Provider One")
                self.assertEqual(found.record["status"], "pending")

                exists = repository.exists("PRV-000001")
                self.assertTrue(exists.metadata["exists"])

                counted = repository.count()
                self.assertEqual(counted.count, 1)

                listed = repository.list_all()
                self.assertEqual(listed.count, 1)
                self.assertEqual(
                    listed.records[0]["provider_id"],
                    "PRV-000001",
                )

                updated = repository.update(
                    "PRV-000001",
                    {"status": "active"},
                )
                self.assertEqual(updated.record["status"], "active")
                self.assertEqual(updated.record["name"], "Provider One")

                deleted = repository.delete("PRV-000001")
                self.assertTrue(deleted.success)
                self.assertEqual(deleted.record_id, "PRV-000001")
                self.assertEqual(repository.count().count, 0)

    def test_multiple_records_preserve_repository_order_across_adapters(
        self,
    ) -> None:
        for backend, _ in ADAPTERS:
            with self.subTest(backend=backend):
                repository = self._build_repository(backend)

                repository.create(
                    {
                        "provider_id": "PRV-000001",
                        "name": "Provider One",
                    }
                )
                repository.create(
                    {
                        "provider_id": "PRV-000002",
                        "name": "Provider Two",
                    }
                )

                listed = repository.list_all()

                self.assertEqual(
                    [
                        record["provider_id"]
                        for record in listed.records
                    ],
                    ["PRV-000001", "PRV-000002"],
                )

    def test_data_persists_across_repository_instances_for_each_adapter(
        self,
    ) -> None:
        for backend, _ in ADAPTERS:
            with self.subTest(backend=backend):
                manager = self._build_manager(backend)
                root = self.storage_root / backend

                first = self.factory.create_local(
                    storage_manager=manager,
                    repository_name="providers",
                    id_field="provider_id",
                    storage_root=root,
                    backend=backend,
                )
                first.create(
                    {
                        "provider_id": "PRV-000001",
                        "name": "Persistent Provider",
                    }
                )

                second = self.factory.create_local(
                    storage_manager=manager,
                    repository_name="providers",
                    id_field="provider_id",
                    storage_root=root,
                    backend=backend,
                )

                found = second.get("PRV-000001")
                self.assertEqual(
                    found.record["name"],
                    "Persistent Provider",
                )
                self.assertEqual(second.count().count, 1)

    def test_explicit_backend_overrides_active_backend(self) -> None:
        manager = self._build_manager("json")

        repository = self.factory.create_local(
            storage_manager=manager,
            repository_name="providers",
            id_field="provider_id",
            storage_root=self.storage_root / "explicit_csv",
            backend="csv",
        )

        repository.create(
            {
                "provider_id": "PRV-000001",
                "name": "CSV Provider",
            }
        )

        self.assertEqual(manager.active_backend, "json")
        self.assertEqual(repository.backend, "csv")
        self.assertEqual(
            repository.get("PRV-000001").record["name"],
            "CSV Provider",
        )

    def test_none_backend_uses_storage_manager_active_backend(self) -> None:
        manager = self._build_manager("jsonl")

        repository = self.factory.create_local(
            storage_manager=manager,
            repository_name="providers",
            id_field="provider_id",
            storage_root=self.storage_root / "active_backend",
            backend=None,
        )

        repository.create(
            {
                "provider_id": "PRV-000001",
                "name": "Active Backend Provider",
            }
        )

        self.assertIsNone(repository.backend)
        self.assertEqual(manager.active_backend, "jsonl")
        self.assertEqual(repository.count().count, 1)

    def test_explicit_backend_is_reported_in_result_metadata(self) -> None:
        for backend, _ in ADAPTERS:
            with self.subTest(backend=backend):
                repository = self._build_repository(backend)
                result = repository.count()

                self.assertEqual(
                    result.metadata["backend"],
                    backend,
                )
                self.assertEqual(
                    result.metadata["repository_type"],
                    "local",
                )

    def test_unknown_backend_is_translated_to_repository_storage_error(
        self,
    ) -> None:
        manager = self._build_manager("json")

        repository = self.factory.create_local(
            storage_manager=manager,
            repository_name="providers",
            id_field="provider_id",
            storage_root=self.storage_root / "unknown",
            backend="unsupported",
        )

        with self.assertRaises(RepositoryCountError) as context:
            repository.count()

        self.assertIsInstance(
            context.exception.__cause__,
            RepositoryStorageError,
        )

        self.assertEqual(
            context.exception.__cause__.repository,
            "providers",
        )

        self.assertEqual(
            context.exception.__cause__.repository_type,
            "local",
        )

        self.assertEqual(
            context.exception.__cause__.metadata["backend"],
            "unsupported",
        )


if __name__ == "__main__":
    unittest.main()
