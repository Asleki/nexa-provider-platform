"""
============================================================
Nexa Provider Platform
File: tests/unit/repositories/test_repository_result.py
Layer: Repository Unit Tests
Milestone: NPP-M005.2 — Repository Result Tests
============================================================

Verifies RepositoryResult validation, normalization, immutability,
factory methods, derived properties, and serialization.
"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError
from types import MappingProxyType

from shared.repositories.repository_result import RepositoryResult
from shared.repositories.repository_types import RepositoryOperation


class RepositoryResultTests(unittest.TestCase):
    """Unit tests for the standardized repository result contract."""

    def test_direct_construction_normalizes_repository_and_record_id(
        self,
    ) -> None:
        result = RepositoryResult(
            success=True,
            operation=RepositoryOperation.READ,
            repository="  providers  ",
            record_id="  PRV-000001  ",
        )

        self.assertEqual(result.repository, "providers")
        self.assertEqual(result.record_id, "PRV-000001")

    def test_empty_repository_name_is_rejected(self) -> None:
        for value in ("", "   "):
            with self.subTest(repository=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "Repository name must not be empty",
                ):
                    RepositoryResult(
                        success=True,
                        operation=RepositoryOperation.COUNT,
                        repository=value,
                    )

    def test_blank_record_id_is_rejected_when_provided(self) -> None:
        for value in ("", "   ", "\t", "\n"):
            with self.subTest(record_id=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "record_id must not be empty when provided",
                ):
                    RepositoryResult(
                        success=True,
                        operation=RepositoryOperation.READ,
                        repository="providers",
                        record_id=value,
                    )

    def test_negative_records_affected_is_rejected(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "records_affected must not be negative",
        ):
            RepositoryResult(
                success=True,
                operation=RepositoryOperation.COUNT,
                repository="providers",
                records_affected=-1,
            )

    def test_result_instance_is_frozen(self) -> None:
        result = RepositoryResult.counted(
            repository="providers",
            count=2,
        )

        with self.assertRaises(FrozenInstanceError):
            result.success = False  # type: ignore[misc]

    def test_record_is_defensively_copied_and_read_only(self) -> None:
        source = {
            "provider_id": "PRV-000001",
            "name": "Provider One",
        }

        result = RepositoryResult.created(
            repository="providers",
            record_id="PRV-000001",
            record=source,
        )

        source["name"] = "Changed Outside Result"

        self.assertIsInstance(result.record, MappingProxyType)
        self.assertEqual(result.record["name"], "Provider One")

        with self.assertRaises(TypeError):
            result.record["name"] = "Changed"  # type: ignore[index]

    def test_records_are_defensively_copied_and_read_only(self) -> None:
        first = {"provider_id": "PRV-000001"}
        second = {"provider_id": "PRV-000002"}

        result = RepositoryResult.listed(
            repository="providers",
            records=(first, second),
        )

        first["provider_id"] = "CHANGED"

        self.assertIsInstance(result.records, tuple)
        self.assertEqual(len(result.records), 2)
        self.assertTrue(
            all(
                isinstance(record, MappingProxyType)
                for record in result.records
            )
        )
        self.assertEqual(
            result.records[0]["provider_id"],
            "PRV-000001",
        )

        with self.assertRaises(TypeError):
            result.records[0]["provider_id"] = "CHANGED"  # type: ignore[index]

    def test_metadata_is_defensively_copied_and_read_only(self) -> None:
        metadata = {"backend": "json"}

        result = RepositoryResult.counted(
            repository="providers",
            count=3,
            metadata=metadata,
        )

        metadata["backend"] = "changed"

        self.assertIsInstance(result.metadata, MappingProxyType)
        self.assertEqual(result.metadata["backend"], "json")
        self.assertEqual(result.metadata["count"], 3)

        with self.assertRaises(TypeError):
            result.metadata["backend"] = "changed"  # type: ignore[index]

    def test_failed_property_reflects_success_flag(self) -> None:
        successful = RepositoryResult(
            success=True,
            operation=RepositoryOperation.READ,
            repository="providers",
        )
        failed = RepositoryResult(
            success=False,
            operation=RepositoryOperation.READ,
            repository="providers",
            message="Read failed.",
        )

        self.assertFalse(successful.failed)
        self.assertTrue(failed.failed)

    def test_count_uses_record_collection_for_list_results(self) -> None:
        result = RepositoryResult(
            success=True,
            operation=RepositoryOperation.LIST,
            repository="providers",
            records=(
                {"provider_id": "PRV-000001"},
                {"provider_id": "PRV-000002"},
            ),
            records_affected=99,
        )

        self.assertEqual(result.count, 2)

    def test_count_uses_records_affected_for_non_list_results(self) -> None:
        result = RepositoryResult(
            success=True,
            operation=RepositoryOperation.COUNT,
            repository="providers",
            records_affected=7,
        )

        self.assertEqual(result.count, 7)

    def test_created_factory_builds_expected_result(self) -> None:
        result = RepositoryResult.created(
            repository="providers",
            record_id="PRV-000001",
            record={
                "provider_id": "PRV-000001",
                "name": "Provider One",
            },
            metadata={"backend": "json"},
        )

        self.assertTrue(result.success)
        self.assertFalse(result.failed)
        self.assertIs(result.operation, RepositoryOperation.CREATE)
        self.assertEqual(result.repository, "providers")
        self.assertEqual(result.record_id, "PRV-000001")
        self.assertEqual(result.records_affected, 1)
        self.assertEqual(result.count, 1)
        self.assertEqual(
            result.message,
            "Repository record created.",
        )
        self.assertEqual(result.metadata["backend"], "json")

    def test_found_factory_builds_expected_result(self) -> None:
        result = RepositoryResult.found(
            repository="providers",
            record_id="PRV-000001",
            record={"provider_id": "PRV-000001"},
        )

        self.assertTrue(result.success)
        self.assertIs(result.operation, RepositoryOperation.READ)
        self.assertEqual(result.records_affected, 1)
        self.assertEqual(
            result.message,
            "Repository record found.",
        )

    def test_updated_factory_builds_expected_result(self) -> None:
        result = RepositoryResult.updated(
            repository="providers",
            record_id="PRV-000001",
            record={
                "provider_id": "PRV-000001",
                "status": "active",
            },
        )

        self.assertTrue(result.success)
        self.assertIs(result.operation, RepositoryOperation.UPDATE)
        self.assertEqual(result.records_affected, 1)
        self.assertEqual(
            result.message,
            "Repository record updated.",
        )

    def test_deleted_factory_builds_expected_result(self) -> None:
        result = RepositoryResult.deleted(
            repository="providers",
            record_id="PRV-000001",
        )

        self.assertTrue(result.success)
        self.assertIs(result.operation, RepositoryOperation.DELETE)
        self.assertIsNone(result.record)
        self.assertEqual(result.records_affected, 1)
        self.assertEqual(
            result.message,
            "Repository record deleted.",
        )

    def test_listed_factory_builds_expected_result(self) -> None:
        result = RepositoryResult.listed(
            repository="providers",
            records=(
                {"provider_id": "PRV-000001"},
                {"provider_id": "PRV-000002"},
            ),
        )

        self.assertTrue(result.success)
        self.assertIs(result.operation, RepositoryOperation.LIST)
        self.assertEqual(result.records_affected, 2)
        self.assertEqual(result.count, 2)
        self.assertEqual(
            result.message,
            "Repository records listed.",
        )

    def test_listed_factory_supports_empty_results(self) -> None:
        result = RepositoryResult.listed(
            repository="providers",
            records=(),
        )

        self.assertTrue(result.success)
        self.assertEqual(result.records, ())
        self.assertEqual(result.records_affected, 0)
        self.assertEqual(result.count, 0)

    def test_existence_checked_factory_for_existing_record(self) -> None:
        result = RepositoryResult.existence_checked(
            repository="providers",
            record_id="PRV-000001",
            exists=True,
            metadata={"backend": "json"},
        )

        self.assertTrue(result.success)
        self.assertIs(result.operation, RepositoryOperation.EXISTS)
        self.assertEqual(result.records_affected, 1)
        self.assertEqual(result.metadata["exists"], True)
        self.assertEqual(result.metadata["backend"], "json")
        self.assertEqual(
            result.message,
            "Repository record exists.",
        )

    def test_existence_checked_factory_for_missing_record(self) -> None:
        result = RepositoryResult.existence_checked(
            repository="providers",
            record_id="PRV-000001",
            exists=False,
        )

        self.assertTrue(result.success)
        self.assertIs(result.operation, RepositoryOperation.EXISTS)
        self.assertEqual(result.records_affected, 0)
        self.assertEqual(result.metadata["exists"], False)
        self.assertEqual(
            result.message,
            "Repository record does not exist.",
        )

    def test_counted_factory_builds_expected_result(self) -> None:
        result = RepositoryResult.counted(
            repository="providers",
            count=5,
            metadata={"backend": "json"},
        )

        self.assertTrue(result.success)
        self.assertIs(result.operation, RepositoryOperation.COUNT)
        self.assertEqual(result.records_affected, 5)
        self.assertEqual(result.count, 5)
        self.assertEqual(result.metadata["count"], 5)
        self.assertEqual(result.metadata["backend"], "json")
        self.assertEqual(
            result.message,
            "Repository records counted.",
        )

    def test_counted_factory_rejects_negative_count(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "count must not be negative",
        ):
            RepositoryResult.counted(
                repository="providers",
                count=-1,
            )

    def test_factory_custom_messages_are_preserved(self) -> None:
        result = RepositoryResult.created(
            repository="providers",
            record_id="PRV-000001",
            record={"provider_id": "PRV-000001"},
            message="Provider created successfully.",
        )

        self.assertEqual(
            result.message,
            "Provider created successfully.",
        )

    def test_to_dict_returns_plain_serializable_structures(self) -> None:
        result = RepositoryResult.listed(
            repository="providers",
            records=(
                {
                    "provider_id": "PRV-000001",
                    "status": "active",
                },
            ),
            metadata={"backend": "json"},
        )

        serialized = result.to_dict()

        self.assertEqual(
            serialized,
            {
                "success": True,
                "operation": "list",
                "repository": "providers",
                "record_id": None,
                "record": None,
                "records": [
                    {
                        "provider_id": "PRV-000001",
                        "status": "active",
                    }
                ],
                "records_affected": 1,
                "message": "Repository records listed.",
                "metadata": {"backend": "json"},
            },
        )

        self.assertIsInstance(serialized["records"], list)
        self.assertIsInstance(serialized["metadata"], dict)

    def test_to_dict_returns_independent_record_and_metadata_copies(
        self,
    ) -> None:
        result = RepositoryResult.created(
            repository="providers",
            record_id="PRV-000001",
            record={
                "provider_id": "PRV-000001",
                "name": "Provider One",
            },
            metadata={"backend": "json"},
        )

        serialized = result.to_dict()
        serialized["record"]["name"] = "Changed"  # type: ignore[index]
        serialized["metadata"]["backend"] = "changed"  # type: ignore[index]

        self.assertEqual(result.record["name"], "Provider One")
        self.assertEqual(result.metadata["backend"], "json")


if __name__ == "__main__":
    unittest.main()
