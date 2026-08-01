# Production Seed Datasets

`database/seeds/` contains version-controlled production seed assets for the Nexa Provider Platform and NexiLabs. These files are not test fixtures, exports, backups, or raw database dumps.

## Governing rule

Production seeds must follow this path:

```text
CSV asset
  -> manifest verification
  -> source-specific Python adapter
  -> existing candidate validation and quarantine
  -> existing controlled importer
  -> repository contract
  -> PostgreSQL adapter
```

Direct SQL imports, PostgreSQL `COPY`, and application logic embedded in terminal commands are prohibited. Python owns source interpretation, canonical normalization, comparison keys, name kinds, runtime selection, sex-usage classification, validation, quarantine, duplicate interpretation, and provenance. PostgreSQL provides durable storage and structural integrity only.

## Dataset families

| Directory | Purpose | Current activation |
|---|---|---|
| `name_catalogue/novegeo/` | Native NoveGeo atomic first, middle, and surname seeds plus tribe references | Atomic names eligible through a future source adapter |
| `name_catalogue/multicultural/` | Reusable international and accented atomic name components | Atomic names eligible through a future source adapter |
| `name_catalogue/immigration/` | Culturally aligned first-name and family-name pairs for foreigners entering NoveGeo | Atomic extraction eligible; formal pair persistence deferred |
| `title_catalogue/` | Titles and honorifics | Reserved; not a `CanonicalName` import source |

## Required governance

Every released dataset family must have a `manifest.json` containing stable dataset and file identities, exact required headers, row counts, SHA-256 checksums, source-to-domain mappings, runtime policy, provenance, activation boundaries, and relationship declarations.

- All files use UTF-8 and comma delimiters.
- Source record IDs remain distinct from canonical name IDs.
- One import batch targets exactly one runtime.
- Eligible runtimes are `simulation` and `production`; no automatic cross-runtime copy is permitted.
- Canonical display values preserve Unicode. Python applies NFC for canonical values and NFKC plus case folding for comparison keys.
- Accent stripping and automatic merging of accented/unaccented records are prohibited unless a later contract explicitly authorizes aliases.
- Released files must not be silently edited. Any content change requires checksum updates and a dataset version or governed revision.
- Production seed assets must contain no real-person records or sensitive personal data.
- Test fixtures belong under `tests/fixtures/` and must be small synthetic subsets, never hidden copies of production seeds.

## Identity boundaries

The following identifiers may coexist and must not be collapsed: dataset ID, file ID, source record ID, source pair ID, import candidate ID, batch ID, canonical name ID, future pair ID, and future tribe/community ID.

A CSV filename or source row ID never becomes a canonical identity by implication. Canonical identity remains governed by the locked Name Catalogue contract: runtime mode, name kind, and Python-produced search value.

## Relationship boundaries

- NoveGeo surname `tribe` values are validated against `novegeo_tribes.csv` and preserved as opaque logical references. This milestone does not create a Tribe Registry.
- Immigration pairs preserve evidence that a first name and surname arrived together. This milestone does not create a full-name-pair table.
- Titles and honorifics remain separate from legal name components and cannot be imported as first, middle, or surname records.
- Origin and language labels are provenance today; future registries may bind them through new adapters or mappings without changing canonical name IDs.

## Release and verification

Before import, Python must verify the manifest schema, exact header spelling and case, row count, checksum, duplicate source IDs, required values, cross-file references, runtime selection, and activation permissions. A failed integrity or relationship check blocks import and must produce an explainable error or quarantine outcome.
