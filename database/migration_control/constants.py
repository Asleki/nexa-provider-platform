"""Stable constants for NPP database migration control."""
from __future__ import annotations
import re
MANIFEST_SCHEMA="npp.database-migration-manifest"; MANIFEST_SCHEMA_VERSION=1; MANIFEST_FILENAME="migration_manifest.json"; SHA256_HEX_LENGTH=64
MIGRATION_FILENAME_PATTERN=re.compile(r"^m(?P<parent>\d{3})_(?P<minor>\d{2})_(?P<leaf>\d{2})_(?P<description>[a-z0-9]+(?:_[a-z0-9]+)*)\.sql$")
ALLOWED_STATIC_FILENAMES=frozenset({".gitkeep",MANIFEST_FILENAME}); TRANSACTION_POLICIES=frozenset({"embedded","runner_managed","none"}); DIRECTIONS=frozenset({"forward","rollback"})
RUNNER_VERSION="1.0.0"; LEDGER_SCHEMA="platform"; LEDGER_TABLE="schema_migration"; LEDGER_QUALIFIED_NAME=f"{LEDGER_SCHEMA}.{LEDGER_TABLE}"
LEDGER_STATUSES=frozenset({"STARTED","APPLIED","FAILED"}); OUTPUT_FORMATS=frozenset({"human","json"}); DEFAULT_POSTGRESQL_PORT=5432; DEFAULT_CONNECT_TIMEOUT=10
SUPPORTED_SSL_MODES=frozenset({"require","verify-ca","verify-full"}); ADVISORY_LOCK_KEY=598083769130013
EXIT_SUCCESS=0; EXIT_OPERATIONAL_FAILURE=1; EXIT_USAGE_ERROR=2; EXIT_INTEGRITY_FAILURE=3; EXIT_DRIFT=4; EXIT_TARGET_MISMATCH=5; EXIT_LOCK_UNAVAILABLE=6; EXIT_EXECUTION_FAILURE=7
__all__=[n for n in globals() if n.isupper()]
