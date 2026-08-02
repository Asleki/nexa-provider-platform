# NPP Verification Journey

This document records only verified milestones.

## Verified
- PostgreSQL SSL connectivity verified.
- Migration ledger verified.
- Read-only adapter qualification passed.
- 8 sampled rows produced 9 candidates.
- Pre-write validation passed.
- First bounded import: 10 imported.
- Read-back verification: 10/10.
- Second bounded import:
  - Imported: 0
  - Already existed: 10
  - Count unchanged: 10.

## Proven Pipeline
ProductionSeedLoader
→ ProductionSeedAdapter
→ NameCandidateValidator
→ NameImportBatch.approve()
→ ControlledNameBatchImporter
→ PostgreSQLNameRepository
→ reference.canonical_name
