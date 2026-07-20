"""
============================================================
Nexa Provider Platform
File: tests/unit/repositories/test_base_repository.py
Layer: Repository Unit Tests
Milestone: NPP-M005.1 — Repository Interface Tests
============================================================

Verifies the storage-independent repository interface contract
and the shared behavior implemented by BaseRepository.
"""

from __future__ import annotations

import inspect
import unittest
from collections.abc import Mapping
from typing import Any

from shared.repositories.base_repository import BaseRepository
from shared.repositories.repository_interface import RepositoryInterface
from shared.repositories.repository_result import RepositoryResult
from shared.repositories.repository_types import (
    RepositoryOperation,
    RepositoryType,
)


class ConcreteRepository(BaseRepository):
    """Minimal concrete repository used only for unit testing."""

    def __init__(
        self,
        repository_name: str = "providers",
        id_field: str = "provider_id",
        repository_type: RepositoryType = RepositoryType.LOCAL,
    ) -> None:
        super().__init__(
            repository_name=repository_name,
            id_field=id_field,
            repository_type=repository_type,
        )

    def create(
        self,
        record: Mapping[str, Any],
    ) -> RepositoryResult:
        record_id = self.validate_identifier(record[self.id_field])
        return RepositoryResult.created(
            repository=self.repository_name,
            record_id=record_id,
            record=record,
        )

    def get(self, record_id: str) -> RepositoryResult:
        normalized_id = self.validate_identifier(record_id)
        return RepositoryResult.found(
            repository=self.repository_name,
            record_id=normalized_id,
            record={self.id_field: normalized_id},
        )

    def update(
        self,
        record_id: str,
        record: Mapping[str, Any],
    ) -> RepositoryResult:
        normalized_id = self.validate_identifier(record_id)
        updated_record = dict(record)
        updated_record[self.id_field] = normalized_id
        return RepositoryResult.updated(
            repository=self.repository_name,
            record_id=normalized_id,
            record=updated_record,
        )

    def delete(self, record_id: str) -> RepositoryResult:
        normalized_id = self.validate_identifier(record_id)
        return RepositoryResult.deleted(
            repository=self.repository_name,
            record_id=normalized_id,
        )

    def list_all(self) -> RepositoryResult:
        return RepositoryResult.listed(
            repository=self.repository_name,
            records=(),
        )

    def exists(self, record_id: str) -> RepositoryResult:
        normalized_id = self.validate_identifier(record_id)
        return RepositoryResult.existence_checked(
            repository=self.repository_name,
            record_id=normalized_id,
            exists=False,
        )

    def count(self) -> RepositoryResult:
        return RepositoryResult.counted(
            repository=self.repository_name,
            count=0,
        )


class IncompleteRepository(BaseRepository):
    """Intentionally incomplete implementation for abstractness tests."""

    pass


class RepositoryInterfaceTests(unittest.TestCase):
    """Tests for RepositoryInterface and BaseRepository contracts."""

    def test_repository_interface_is_abstract(self) -> None:
        self.assertTrue(inspect.isabstract(RepositoryInterface))

        with self.assertRaises(TypeError):
            RepositoryInterface()  # type: ignore[abstract]

    def test_base_repository_is_abstract(self) -> None:
        self.assertTrue(inspect.isabstract(BaseRepository))

        with self.assertRaises(TypeError):
            BaseRepository(  # type: ignore[abstract]
                repository_name="providers",
                id_field="provider_id",
            )

    def test_incomplete_subclass_cannot_be_instantiated(self) -> None:
        self.assertTrue(inspect.isabstract(IncompleteRepository))

        with self.assertRaises(TypeError):
            IncompleteRepository(
                repository_name="providers",
                id_field="provider_id",
            )

    def test_interface_declares_expected_abstract_members(self) -> None:
        expected_members = {
            "repository_name",
            "repository_type",
            "id_field",
            "create",
            "get",
            "update",
            "delete",
            "list_all",
            "exists",
            "count",
        }

        self.assertEqual(
            set(RepositoryInterface.__abstractmethods__),
            expected_members,
        )

    def test_interface_method_signatures_are_stable(self) -> None:
        expected_parameter_names = {
            "create": ("self", "record"),
            "get": ("self", "record_id"),
            "update": ("self", "record_id", "record"),
            "delete": ("self", "record_id"),
            "list_all": ("self",),
            "exists": ("self", "record_id"),
            "count": ("self",),
        }

        for method_name, parameter_names in expected_parameter_names.items():
            with self.subTest(method=method_name):
                method = getattr(RepositoryInterface, method_name)
                actual_names = tuple(
                    inspect.signature(method).parameters
                )
                self.assertEqual(actual_names, parameter_names)

    def test_complete_subclass_is_concrete(self) -> None:
        self.assertFalse(inspect.isabstract(ConcreteRepository))

        repository = ConcreteRepository()

        self.assertIsInstance(repository, RepositoryInterface)
        self.assertIsInstance(repository, BaseRepository)

    def test_metadata_is_normalized(self) -> None:
        repository = ConcreteRepository(
            repository_name="  providers  ",
            id_field="  provider_id  ",
        )

        self.assertEqual(repository.repository_name, "providers")
        self.assertEqual(repository.id_field, "provider_id")
        self.assertEqual(
            repository.repository_type,
            RepositoryType.LOCAL.value,
        )

    def test_repository_name_is_required(self) -> None:
        invalid_values = ("", "   ")

        for value in invalid_values:
            with self.subTest(repository_name=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "repository_name must not be empty",
                ):
                    ConcreteRepository(repository_name=value)

    def test_id_field_is_required(self) -> None:
        invalid_values = ("", "   ")

        for value in invalid_values:
            with self.subTest(id_field=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "id_field must not be empty",
                ):
                    ConcreteRepository(id_field=value)

    def test_validate_identifier_accepts_valid_string(self) -> None:
        repository = ConcreteRepository()

        self.assertEqual(
            repository.validate_identifier("PRV-000001"),
            "PRV-000001",
        )

    def test_validate_identifier_trims_whitespace(self) -> None:
        repository = ConcreteRepository()

        self.assertEqual(
            repository.validate_identifier("  PRV-000001  "),
            "PRV-000001",
        )

    def test_validate_identifier_rejects_none(self) -> None:
        repository = ConcreteRepository()

        with self.assertRaisesRegex(
            ValueError,
            "record_id must not be None",
        ):
            repository.validate_identifier(None)

    def test_validate_identifier_rejects_blank_strings(self) -> None:
        repository = ConcreteRepository()

        for value in ("", "   ", "\t", "\n"):
            with self.subTest(record_id=value):
                with self.assertRaisesRegex(
                    ValueError,
                    "record_id must not be empty",
                ):
                    repository.validate_identifier(value)

    def test_validate_identifier_rejects_non_strings(self) -> None:
        repository = ConcreteRepository()
        invalid_values = (
            123,
            True,
            3.14,
            ["PRV-000001"],
            {"id": "PRV-000001"},
            object(),
        )

        for value in invalid_values:
            with self.subTest(record_id=value):
                with self.assertRaisesRegex(
                    TypeError,
                    "record_id must be a string",
                ):
                    repository.validate_identifier(value)

    def test_concrete_methods_return_repository_results(self) -> None:
        repository = ConcreteRepository()

        results = (
            repository.create(
                {
                    "provider_id": "PRV-000001",
                    "name": "Test Provider",
                }
            ),
            repository.get("PRV-000001"),
            repository.update(
                "PRV-000001",
                {"name": "Updated Provider"},
            ),
            repository.delete("PRV-000001"),
            repository.list_all(),
            repository.exists("PRV-000001"),
            repository.count(),
        )

        for result in results:
            with self.subTest(operation=result.operation):
                self.assertIsInstance(result, RepositoryResult)
                self.assertTrue(result.success)

    def test_concrete_methods_use_expected_operations(self) -> None:
        repository = ConcreteRepository()

        operation_results = {
            RepositoryOperation.CREATE: repository.create(
                {"provider_id": "PRV-000001"}
            ),
            RepositoryOperation.READ: repository.get("PRV-000001"),
            RepositoryOperation.UPDATE: repository.update(
                "PRV-000001",
                {"name": "Updated"},
            ),
            RepositoryOperation.DELETE: repository.delete("PRV-000001"),
            RepositoryOperation.LIST: repository.list_all(),
            RepositoryOperation.EXISTS: repository.exists("PRV-000001"),
            RepositoryOperation.COUNT: repository.count(),
        }

        for expected_operation, result in operation_results.items():
            with self.subTest(operation=expected_operation):
                self.assertIs(result.operation, expected_operation)


if __name__ == "__main__":
    unittest.main()
