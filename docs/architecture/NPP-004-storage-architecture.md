# NPP-004 — Storage Architecture

**Document ID:** NPP-004  
**Title:** Storage Architecture  
**Project:** Nexa Provider Platform (NPP)  
**Status:** Draft  
**Version:** 0.1.0  
**Author:** NexTech Kenya Limited  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines how provider data is stored, accessed, synchronized and migrated throughout the lifecycle of the Nexa Provider Platform.

The storage architecture is designed to support offline-first development while allowing future migration to cloud-based storage without modifying provider business logic.

---

# 2. Storage Principles

The storage layer shall be:

- Offline first
- Technology independent
- Replaceable
- Versioned
- Auditable
- Synchronization ready
- Deterministic
- Modular

Provider services must never depend directly on a storage technology.

---

# 3. Storage Evolution

The platform storage evolves in three phases.

## Phase 1

Local Storage

```text
Provider CLI
        │
        ▼
Provider Services
        │
        ▼
Repository Layer
        │
        ▼
JSON / JSONL / CSV
```

This is the current implementation.

---

## Phase 2

Hybrid Storage

```text
Provider CLI
        │
        ▼
Provider Services
        │
        ▼
Repository Layer
       ╱ ╲
      ╱   ╲
 JSON      Supabase
```

Both storage implementations may coexist.

---

## Phase 3

Cloud Storage

```text
Provider CLI
        │
        ▼
Provider Services
        │
        ▼
Repository Layer
        │
        ▼
Supabase PostgreSQL
```

Local storage continues to support:

- testing
- backups
- exports
- seed data
- offline development

---

# 4. Repository Layer

Provider services communicate only with repository interfaces.

They never read or write storage directly.

```text
Provider Service
        │
        ▼
Registry Repository
        │
 ┌──────┴────────┐
 │               │
 ▼               ▼
JSON        Supabase
Adapter      Adapter
```

Changing storage technology must not require changes to provider business logic.

---

# 5. Storage Types

The platform uses several storage categories.

## Operational Records

Current:

- JSON

Future:

- PostgreSQL

Examples:

- Citizens
- Businesses
- Banks
- Accounts
- Wallets
- SIM registrations

---

## Event Storage

Current:

- JSONL

Purpose:

Immutable provider events.

Examples:

```text
storage/events/provider-events.jsonl
```

---

## Audit Storage

Current:

- JSONL

Purpose:

Immutable audit history.

Examples:

```text
storage/audit/provider-audit.jsonl
```

---

## Export Storage

Purpose:

Generate portable datasets.

Formats:

- CSV
- JSON

Examples:

```text
storage/exports/
```

---

## Backup Storage

Purpose:

Recovery.

Examples:

```text
storage/backups/
```

---

## Seed Storage

Purpose:

Development fixtures.

Examples:

```text
storage/seeds/
```

---

# 6. Directory Structure

```text
storage/
├── json/
├── csv/
├── events/
├── audit/
├── exports/
├── backups/
├── seeds/
└── sync/
```

---

# 7. JSON Storage

JSON is the primary storage during Phase 1.

Examples:

```text
storage/json/citizens.json
storage/json/businesses.json
storage/json/banks.json
storage/json/accounts.json
storage/json/wallets.json
storage/json/sims.json
```

JSON files store the latest provider state.

---

# 8. JSONL Storage

JSONL stores immutable records.

Examples:

```text
storage/events/provider-events.jsonl

storage/audit/provider-audit.jsonl
```

New records are appended.

Existing records must never be modified.

---

# 9. CSV Storage

CSV files are intended for:

- reporting
- exports
- interoperability
- backups

CSV files are not the primary operational storage.

---

# 10. Synchronization

Synchronization is introduced after Supabase becomes available.

Current phase:

```text
JSON
```

Future phase:

```text
JSON
      │
Synchronization
      │
Supabase
```

Synchronization must support:

- retries
- idempotency
- conflict detection
- reconciliation
- audit logging

---

# 11. Storage Independence

Provider services must never perform operations such as:

```python
open(...)
```

or

```python
json.dump(...)
```

Instead:

```text
Provider Service
        │
        ▼
Repository Interface
        │
        ▼
Storage Adapter
```

This allows new storage technologies to be introduced without changing provider business logic.

---

# 12. Future Cloud Storage

When Supabase is introduced, it becomes the shared provider registry.

Google Cloud is reserved for:

- analytics
- approved AI datasets
- long-term archival

Google Cloud is not the operational provider database.

---

# 13. Guiding Principle

Storage is an implementation detail.

Provider services own business logic.

Storage adapters own persistence.

This separation ensures the platform remains portable, testable and maintainable throughout its evolution.