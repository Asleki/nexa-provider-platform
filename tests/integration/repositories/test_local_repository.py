"""
============================================================
Nexa Provider Platform
File: tests/integration/repositories/test_local_repository.py
Layer: Repository Integration Tests
Milestone: NPP-M005.7 — Local Repository Integration
============================================================

Verifies that RepositoryFactory, RepositoryRegistry,
LocalRepository, StorageManager, and JsonStorage work together
through real filesystem-backed JSON persistence.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from shared.repositories.local_repository import LocalRepository
from shared.repositories.repository_errors import (
    RepositoryDuplicateRecordError,
    RepositoryRecordNotFoundError,
)
from shared.repositories.repository_factory import RepositoryFactory
from shared.repositories.repository_types import (
    RepositoryOperation,
    RepositoryType,
)
from shared.storage.json_storage import JsonStorage
from shared.storage.storage_manager import StorageManager


class LocalRepositoryIntegrationTests(unittest.TestCase):
    """End-to-end integration tests for the local repository backend."""

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.storage_root = Path(self.temporary_directory.name)

        self.storage_manager = StorageManager()
        self.storage_manager.register_adapter(
            JsonStorage(),
            make_default=True,
        )

        self.factory = RepositoryFactory()
        self.repository = self.factory.create_local(
            storage_manager=self.storage_manager,
            repository_name="providers",
            id_field="provider_id",
            storage_root=self.storage_root,
            backend="json",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_factory_creates_configured_local_repository(self) -> None:
        self.assertIsInstance(self.repository, LocalRepository)
        self.assertEqual(self.repository.repository_name, "providers")
        self.assertEqual(self.repository.id_field, "provider_id")
        self.assertEqual(
            self.repository.repository_type,
            RepositoryType.LOCAL.value,
        )
        self.assertEqual(self.repository.backend, "json")
        self.assertEqual(
            self.repository.collection_path,
            self.storage_root / "providers.json",
        )
        self.assertEqual(self.storage_manager.active_backend, "json")

    def test_empty_repository_returns_successful_empty_results(self) -> None:
        listed = self.repository.list_all()
        counted = self.repository.count()
        exists = self.repository.exists("PRV-000001")

        self.assertTrue(listed.success)
        self.assertIs(listed.operation, RepositoryOperation.LIST)
        self.assertEqual(listed.records, ())
        self.assertEqual(listed.count, 0)

        self.assertTrue(counted.success)
        self.assertIs(counted.operation, RepositoryOperation.COUNT)
        self.assertEqual(counted.count, 0)
        self.assertEqual(counted.metadata["count"], 0)

        self.assertTrue(exists.success)
        self.assertIs(exists.operation, RepositoryOperation.EXISTS)
        self.assertFalse(exists.metadata["exists"])

    def test_create_persists_record_to_json_storage(self) -> None:
        result = self.repository.create(
            {
                "provider_id": "PRV-000001",
                "name": "Provider One",
                "status": "active",
            }
        )

        self.assertTrue(result.success)
        self.assertIs(result.operation, RepositoryOperation.CREATE)
        self.assertEqual(result.record_id, "PRV-000001")
        self.assertEqual(result.record["name"], "Provider One")
        self.assertEqual(result.metadata["repository_type"], "local")
        self.assertEqual(result.metadata["backend"], "json")
        self.assertTrue(self.repository.collection_path.exists())

        persisted = json.loads(
            self.repository.collection_path.read_text(encoding="utf-8")
        )

        self.assertEqual(
            persisted,
            [
                {
                    "name": "Provider One",
                    "provider_id": "PRV-000001",
                    "status": "active",
                }
            ],
        )

    def test_create_then_get_returns_persisted_record(self) -> None:
        self.repository.create(
            {
                "provider_id": "PRV-000001",
                "name": "Provider One",
            }
        )

        result = self.repository.get("PRV-000001")

        self.assertTrue(result.success)
        self.assertIs(result.operation, RepositoryOperation.READ)
        self.assertEqual(result.record_id, "PRV-000001")
        self.assertEqual(
            dict(result.record),
            {
                "provider_id": "PRV-000001",
                "name": "Provider One",
            },
        )

    def test_multiple_records_can_be_listed_and_counted(self) -> None:
        self.repository.create(
            {
                "provider_id": "PRV-000001",
                "name": "Provider One",
            }
        )
        self.repository.create(
            {
                "provider_id": "PRV-000002",
                "name": "Provider Two",
            }
        )

        listed = self.repository.list_all()
        counted = self.repository.count()

        self.assertEqual(listed.count, 2)
        self.assertEqual(counted.count, 2)
        self.assertEqual(
            [record["provider_id"] for record in listed.records],
            ["PRV-000001", "PRV-000002"],
        )

    def test_partial_update_preserves_existing_fields(self) -> None:
        self.repository.create(
            {
                "provider_id": "PRV-000001",
                "name": "Provider One",
                "status": "pending",
                "region": "north",
            }
        )

        updated = self.repository.update(
            "PRV-000001",
            {
                "status": "active",
            },
        )

        self.assertTrue(updated.success)
        self.assertIs(updated.operation, RepositoryOperation.UPDATE)
        self.assertEqual(updated.record["provider_id"], "PRV-000001")
        self.assertEqual(updated.record["name"], "Provider One")
        self.assertEqual(updated.record["status"], "active")
        self.assertEqual(updated.record["region"], "north")

        persisted = self.repository.get("PRV-000001")
        self.assertEqual(persisted.record["status"], "active")
        self.assertEqual(persisted.record["name"], "Provider One")

    def test_delete_removes_record_and_updates_repository_state(self) -> None:
        self.repository.create(
            {
                "provider_id": "PRV-000001",
                "name": "Provider One",
            }
        )

        deleted = self.repository.delete("PRV-000001")

        self.assertTrue(deleted.success)
        self.assertIs(deleted.operation, RepositoryOperation.DELETE)
        self.assertEqual(deleted.record_id, "PRV-000001")
        self.assertFalse(
            self.repository.exists("PRV-000001").metadata["exists"]
        )
        self.assertEqual(self.repository.count().count, 0)

        with self.assertRaises(RepositoryRecordNotFoundError):
            self.repository.get("PRV-000001")

    def test_duplicate_identifier_is_rejected_without_overwriting_data(
        self,
    ) -> None:
        original = {
            "provider_id": "PRV-000001",
            "name": "Original Provider",
        }
        self.repository.create(original)

        with self.assertRaises(RepositoryDuplicateRecordError):
            self.repository.create(
                {
                    "provider_id": "PRV-000001",
                    "name": "Replacement Provider",
                }
            )

        stored = self.repository.get("PRV-000001")
        self.assertEqual(stored.record["name"], "Original Provider")
        self.assertEqual(self.repository.count().count, 1)

    def test_data_persists_across_repository_instances(self) -> None:
        self.repository.create(
            {
                "provider_id": "PRV-000001",
                "name": "Persistent Provider",
                "status": "active",
            }
        )

        second_repository = self.factory.create(
            RepositoryType.LOCAL,
            storage_manager=self.storage_manager,
            repository_name="providers",
            id_field="provider_id",
            storage_root=self.storage_root,
            backend="json",
        )

        found = second_repository.get("PRV-000001")

        self.assertIsInstance(second_repository, LocalRepository)
        self.assertEqual(found.record["name"], "Persistent Provider")
        self.assertEqual(found.record["status"], "active")
        self.assertEqual(second_repository.count().count, 1)

    def test_two_repository_collections_remain_isolated(self) -> None:
        employees = self.factory.create_local(
            storage_manager=self.storage_manager,
            repository_name="employees",
            id_field="employee_id",
            storage_root=self.storage_root,
            backend="json",
        )

        self.repository.create(
            {
                "provider_id": "PRV-000001",
                "name": "Provider One",
            }
        )
        employees.create(
            {
                "employee_id": "EMP-000001",
                "name": "Employee One",
            }
        )

        self.assertEqual(self.repository.count().count, 1)
        self.assertEqual(employees.count().count, 1)
        self.assertTrue((self.storage_root / "providers.json").exists())
        self.assertTrue((self.storage_root / "employees.json").exists())

        self.assertEqual(
            self.repository.list_all().records[0]["provider_id"],
            "PRV-000001",
        )
        self.assertEqual(
            employees.list_all().records[0]["employee_id"],
            "EMP-000001",
        )

    def test_result_metadata_identifies_storage_configuration(self) -> None:
        result = self.repository.count()

        self.assertEqual(result.metadata["repository_type"], "local")
        self.assertEqual(result.metadata["backend"], "json")
        self.assertEqual(
            result.metadata["collection_path"],
            str(self.storage_root / "providers.json"),
        )


if __name__ == "__main__":
    unittest.main()
