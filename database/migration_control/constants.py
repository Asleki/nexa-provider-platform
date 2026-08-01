"""Constants for M009.13 Bundle A migration catalogue governance."""
from __future__ import annotations

import re

MANIFEST_SCHEMA = "npp.database-migration-manifest"
MANIFEST_SCHEMA_VERSION = 1
MANIFEST_FILENAME = "migration_manifest.json"
SHA256_HEX_LENGTH = 64
MIGRATION_FILENAME_PATTERN = re.compile(
    r"^m(?P<parent>\d{3})_(?P<minor>\d{2})_(?P<leaf>\d{2})_"
    r"(?P<description>[a-z0-9]+(?:_[a-z0-9]+)*)\.sql$"
)
ALLOWED_STATIC_FILENAMES = frozenset({".gitkeep", MANIFEST_FILENAME})
TRANSACTION_POLICIES = frozenset({"embedded", "runner_managed", "none"})
DIRECTIONS = frozenset({"forward", "rollback"})

__all__ = [
    "MANIFEST_SCHEMA",
    "MANIFEST_SCHEMA_VERSION",
    "MANIFEST_FILENAME",
    "SHA256_HEX_LENGTH",
    "MIGRATION_FILENAME_PATTERN",
    "ALLOWED_STATIC_FILENAMES",
    "TRANSACTION_POLICIES",
    "DIRECTIONS",
]
