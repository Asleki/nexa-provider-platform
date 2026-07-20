"""
Nexa Provider Platform
Unit Tests: Repository Errors
Milestone: NPP-M005.3
"""

import unittest

from shared.repositories.repository_errors import (
    REPOSITORY_ERROR_PREFIX,
    RepositoryError,
    RepositoryConfigurationError,
    RepositoryInitializationError,
    RepositoryOperationError,
    RepositoryCreateError,
    RepositoryReadError,
    RepositoryUpdateError,
    RepositoryDeleteError,
    RepositoryListError,
    RepositoryExistsError,
    RepositoryCountError,
    RepositoryRecordError,
    RepositoryRecordNotFoundError,
    RepositoryDuplicateRecordError,
    RepositoryInvalidRecordError,
    RepositoryIdentifierError,
    RepositoryImmutableIdentifierError,
    RepositoryRegistrationError,
    RepositoryAlreadyRegisteredError,
    RepositoryNotRegisteredError,
    RepositoryFactoryError,
    RepositoryUnsupportedOperationError,
    RepositoryStorageError,
    RepositoryDataCorruptionError,
    RepositorySchemaError,
    _normalize_operation,
)
from shared.repositories.repository_types import RepositoryOperation


class RepositoryErrorTests(unittest.TestCase):

    def test_normalize_operation(self):
        self.assertEqual(_normalize_operation(RepositoryOperation.CREATE), "create")
        self.assertEqual(_normalize_operation(" read "), "read")
        self.assertIsNone(_normalize_operation(""))
        self.assertIsNone(_normalize_operation(None))

    def test_default_message(self):
        err = RepositoryError("")
        self.assertEqual(err.message, "RepositoryError")

    def test_to_dict(self):
        cause = ValueError("boom")
        err = RepositoryError(
            "Failure",
            operation=RepositoryOperation.READ,
            repository=" citizens ",
            record_id=" 123 ",
            repository_type=" local ",
            cause=cause,
            metadata={"a": 1},
        )
        d = err.to_dict()
        self.assertEqual(d["operation"], "read")
        self.assertEqual(d["repository"], "citizens")
        self.assertEqual(d["record_id"], "123")
        self.assertEqual(d["repository_type"], "local")
        self.assertEqual(d["cause"], "ValueError")
        self.assertEqual(d["metadata"], {"a": 1})

    def test_metadata_defensive_copy(self):
        md = {"x": 1}
        err = RepositoryError("x", metadata=md)
        md["x"] = 2
        self.assertEqual(err.metadata["x"], 1)

    def test_error_codes_unique(self):
        classes = [
            RepositoryError,
            RepositoryConfigurationError,
            RepositoryInitializationError,
            RepositoryOperationError,
            RepositoryCreateError,
            RepositoryReadError,
            RepositoryUpdateError,
            RepositoryDeleteError,
            RepositoryListError,
            RepositoryExistsError,
            RepositoryCountError,
            RepositoryRecordError,
            RepositoryRecordNotFoundError,
            RepositoryDuplicateRecordError,
            RepositoryInvalidRecordError,
            RepositoryIdentifierError,
            RepositoryImmutableIdentifierError,
            RepositoryRegistrationError,
            RepositoryAlreadyRegisteredError,
            RepositoryNotRegisteredError,
            RepositoryFactoryError,
            RepositoryUnsupportedOperationError,
            RepositoryStorageError,
            RepositoryDataCorruptionError,
            RepositorySchemaError,
        ]
        codes = [c.error_code for c in classes]
        self.assertEqual(len(codes), len(set(codes)))
        for code in codes:
            self.assertTrue(code.startswith(REPOSITORY_ERROR_PREFIX))


if __name__ == "__main__":
    unittest.main()
