"""
Nexa Provider Platform
Unit Tests: Repository Types
Milestone: NPP-M005.6
"""

import unittest

from shared.repositories.repository_types import (
    RepositoryOperation,
    RepositoryType,
)


class RepositoryTypesTests(unittest.TestCase):

    def test_repository_operation_values(self):
        self.assertEqual(RepositoryOperation.CREATE.value, "create")
        self.assertEqual(RepositoryOperation.READ.value, "read")
        self.assertEqual(RepositoryOperation.UPDATE.value, "update")
        self.assertEqual(RepositoryOperation.DELETE.value, "delete")
        self.assertEqual(RepositoryOperation.LIST.value, "list")
        self.assertEqual(RepositoryOperation.EXISTS.value, "exists")
        self.assertEqual(RepositoryOperation.COUNT.value, "count")

    def test_repository_operation_members_are_strings(self):
        for operation in RepositoryOperation:
            self.assertIsInstance(operation, str)
            self.assertIsInstance(operation.value, str)

    def test_repository_operation_member_order(self):
        self.assertEqual(
            tuple(RepositoryOperation),
            (
                RepositoryOperation.CREATE,
                RepositoryOperation.READ,
                RepositoryOperation.UPDATE,
                RepositoryOperation.DELETE,
                RepositoryOperation.LIST,
                RepositoryOperation.EXISTS,
                RepositoryOperation.COUNT,
            ),
        )

    def test_repository_operation_values_are_unique(self):
        values = [
            operation.value
            for operation in RepositoryOperation
        ]

        self.assertEqual(
            len(values),
            len(set(values)),
        )

    def test_repository_type_local_value(self):
        self.assertEqual(
            RepositoryType.LOCAL.value,
            "local",
        )

    def test_repository_type_members_are_strings(self):
        for repository_type in RepositoryType:
            self.assertIsInstance(repository_type, str)
            self.assertIsInstance(repository_type.value, str)

    def test_repository_type_members(self):
        self.assertEqual(
            tuple(RepositoryType),
            (
                RepositoryType.LOCAL,
            ),
        )

    def test_repository_type_values_are_unique(self):
        values = [
            repository_type.value
            for repository_type in RepositoryType
        ]

        self.assertEqual(
            len(values),
            len(set(values)),
        )


if __name__ == "__main__":
    unittest.main()