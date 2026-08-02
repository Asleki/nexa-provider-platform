# M008.13 — Multicultural First Names Qualification Journey

This document records only the verified qualification evidence for the governed Multicultural First Names dataset.

## Objective

Qualify the first bounded live import of multicultural first names into the Nexa Provider Platform development PostgreSQL database, prove idempotent rerun behavior, and verify that the real stored rows preserve their governed source provenance and unresolved multicultural metadata without introducing premature registry references.

## Dataset Information

- Milestone: `M008.13`
- Dataset ID: `dataset.novegeo.name_catalogue.multicultural.v001`
- Dataset family: `multicultural_atomic`
- Runtime mode: `simulation`
- Environment: `development`
- Database: `npp_dev`
- PostgreSQL schema: `reference`
- PostgreSQL table: `canonical_name`
- Repository revision used for qualification: `c3d4feacdda746a8cf6d6efc7f78a96356aae847`
- Requested bounded sample: `10`
- Target name kind: `first_name`

## Source File

- Manifest: `database/seeds/name_catalogue/multicultural/manifest.json`
- File ID: `file.novegeo.multicultural.first_names.v001`
- Governed source path: `name_catalogue/multicultural/multicultural_first_names.csv`
- Import enabled: `true`
- Target kind: `first_name`
- Expected source metadata:
  - `source_family = multicultural_atomic`
  - non-empty `origin_label`
  - non-empty `language_label`
  - `reference_state = unresolved`
  - empty `culture_refs`

The unresolved state is intentional. The source labels are preserved as governed metadata but are not yet converted into foreign references to future language, culture, country, or origin registries.

## Validation Steps

The qualification followed the established verification playbook:

1. Confirmed the repository was on `main` and synchronized.
2. Set the PostgreSQL development connection environment.
3. Confirmed no PostgreSQL password was stored in environment variables.
4. Corrected the manifest path from the native manifest to the multicultural manifest before import.
5. Verified the baseline PostgreSQL counts.
6. Confirmed zero existing multicultural first-name rows for this dataset and source.
7. Extended the reusable temporary qualifier to validate multicultural metadata before import.
8. Compiled the qualifier successfully with `python -m py_compile`.
9. Executed a bounded controlled import of 10 candidates.
10. Read every successful result back through `PostgreSQLNameRepository`.
11. Re-ran the identical batch to prove idempotency.
12. Queried and displayed the real stored PostgreSQL records in read-only mode.

## Qualification Execution

### Pre-import baseline

```text
first_name           simulation      10
middle_name          simulation      10
surname              simulation      10

Simulation multicultural first-name count: 0
Database writes performed: 0
```

### First bounded import

```text
Batch ID: namebatch:e8758979e83ad2bc95d2168f
Candidates: 10
Approved: True
Imported: 10
Already existed: 0
Failed: 0
Complete: True
Count before: 30
Count after: 40
Count delta: 10
Stored or resolved: 10
Final canonical-name count: 40
Target kind: first_name
Runtime: simulation
Database: npp_dev
```

### Qualification result

```text
BOUNDED NAME IMPORT QUALIFICATION: PASSED
```

The first bounded run proved that all 10 approved multicultural first-name candidates were stored, read back, and reconciled with the exact database count increase.

## Idempotent Verification

The same qualifier was executed again using the same manifest, source file, runtime, target kind, and deterministic batch identity.

```text
Batch ID: namebatch:e8758979e83ad2bc95d2168f
Imported: 0
Already existed: 10
Failed: 0
Complete: True
Count before: 40
Count after: 40
Count delta: 0
Stored or resolved: 10
Previously existing: 10
Final canonical-name count: 40
```

### Idempotency conclusion

- Duplicate detection worked for all 10 candidates.
- No duplicate canonical rows were created.
- Existing canonical name IDs were resolved correctly.
- The database count remained unchanged.
- The same semantic identity remained stable under repeat execution.

## PostgreSQL Read-back Verification

The stored rows were queried directly from:

```text
reference.canonical_name
```

The read-only verification required every displayed row to preserve:

- `name_kind = first_name`
- `runtime_mode = simulation`
- `status = active`
- `source_reference = dataset.novegeo.name_catalogue.multicultural.v001`
- `attributes.seed.file_id = file.novegeo.multicultural.first_names.v001`
- `attributes.seed.source_family = multicultural_atomic`
- non-empty `origin_label`
- non-empty `language_label`
- `reference_state = unresolved`
- `culture_refs = []`
- source-record traceability
- sex-usage metadata

The command ended with:

```text
MULTICULTURAL FIRST-NAME DISPLAY VERIFICATION: PASSED
Displayed records: 10
Database writes performed: 0
```

## Verified Stored Names

| Source Record | Name ID | Canonical Value | Origin Label | Language Label | Sex Usage | Reference State | Culture Refs |
|---:|---|---|---|---|---|---|---|
| 1 | `name:8f8ce4727ae4e577a4e99d57` | Klaus | Germany | German | male | unresolved | `[]` |
| 2 | `name:7c2abc45ecca6d50407bcb4f` | Izand | Spanish | Spanish | male | unresolved | `[]` |
| 3 | `name:bf82532ff0d7c28ec9fcafc1` | Penelope | American | English | female | unresolved | `[]` |
| 4 | `name:fdd00106f3291ea651d46fa9` | Kudakwashe | Zimbabwean | Shona | male | unresolved | `[]` |
| 5 | `name:c1410174476b725848b2485e` | Memory | Zimbabwean | Shona | female | unresolved | `[]` |
| 6 | `name:79680c846d172cbc12254241` | Margarita | Spanish | Spanish | female | unresolved | `[]` |
| 7 | `name:b091daa510e2bc67d7e85b59` | Kofi | Ghana | Akan | male | unresolved | `[]` |
| 8 | `name:266cd08baacff3a6856cf39b` | Precious | South African | Zulu | female | unresolved | `[]` |
| 9 | `name:e91fb58bb6657b79f16edd27` | Bin | Chinese | Mandarin | male | unresolved | `[]` |
| 10 | `name:8dfc4e991c83a8a7bc1081b4` | Denise | Cameroon | French | female | unresolved | `[]` |

## Evidence Summary

| Evidence | Verified Result |
|---|---:|
| Baseline multicultural first-name count | 0 |
| Candidates approved | 10 |
| First-run imported | 10 |
| First-run existing | 0 |
| First-run failed | 0 |
| First-run count delta | 10 |
| Idempotent rerun imported | 0 |
| Idempotent rerun existing | 10 |
| Idempotent rerun failed | 0 |
| Idempotent rerun count delta | 0 |
| Direct PostgreSQL rows displayed | 10 |
| Read-back records verified | 10/10 |
| Final canonical-name count | 40 |
| Display-query writes | 0 |

## Production Readiness Decision

### Decision: QUALIFIED for this bounded development operation

The Multicultural First Names source passed the bounded live qualification in the `npp_dev` development database under `simulation` runtime.

This decision proves the current path is suitable for controlled, resumable, idempotent development imports of this governed source. It does not claim that the entire 800-row source has been imported or that unresolved origin and language labels have already been linked to future registries.

## Lessons Learned

1. **Manifest selection must be verified before execution.** The source file ID belonged to the multicultural manifest, not the native manifest. The mismatch was corrected before running the importer.
2. **Unresolved metadata is not missing metadata.** `origin_label` and `language_label` were intentionally preserved while `culture_refs` remained empty.
3. **Premature foreign references would be incorrect.** Future country, culture, and language registries may resolve these labels later without changing the canonical name identity.
4. **The reusable qualifier can be extended safely.** Native surname safeguards remained available while multicultural-specific checks were added without changing repository production files.
5. **A successful import report is insufficient on its own.** Count reconciliation, item-level read-back, idempotent rerun, and direct PostgreSQL display were all required.
6. **Semantic identity remained stable across source families.** Multicultural first names coexist with native first names under the same `first_name` kind while retaining distinct provenance.
7. **No repository code was changed for this qualification.** Only a temporary `/tmp` qualifier was extended and executed.

## Stage, Commit, and Push

After placing this new document at:

```text
verification/0006_MULTICULTURAL_FIRST_NAMES_QUALIFICATION_JOURNEY.md
```

run:

```bash
git status

git add verification/0006_MULTICULTURAL_FIRST_NAMES_QUALIFICATION_JOURNEY.md

git diff --cached

git commit -m "docs(verification): add M008.13 Multicultural First Names qualification journey"

git push origin main

git status
```

Expected final repository state:

```text
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

`CHANGELOG.txt` from the delivery ZIP is an external build-history artifact and is not intended to be copied into the repository.

## Next Dataset

```text
✅ Native First Names
✅ Native Middle Names
✅ Native Surnames
✅ Multicultural First Names
🔁 Multicultural Accented First Names
⬜ Multicultural Family Names
⬜ Multicultural Accented Family Names
⬜ Immigration Paired Names
```

The next qualification must additionally prove that accented Unicode characters survive manifest loading, candidate adaptation, normalization, PostgreSQL persistence, idempotent rerun, and read-back without loss or unintended transliteration.
