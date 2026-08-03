# M008.17 — Immigration Paired Names Qualification Journey

## Objective

Qualify the governed import of ten Immigration Paired Name source rows and prove that:

- each governed source row produces exactly two candidates;
- each pair contains one `first_name` and one `surname`;
- both candidates share one governed `source_record_id`;
- `component_role` matches the candidate name kind;
- semantic canonical deduplication works correctly;
- PostgreSQL persistence and read-back succeed;
- idempotent reruns create no duplicates;
- cross-source semantic reuse is detected and explained accurately.

## Dataset Information

| Field | Verified value |
|---|---|
| Dataset ID | `dataset.novegeo.name_catalogue.immigration.v001` |
| Source family | `immigration_paired_names` |
| Runtime mode | `simulation` |
| Source rows qualified | `10` |
| Candidate components | `20` |
| Candidate kinds | `10 first_name`, `10 surname` |
| Database | `npp_dev` |
| PostgreSQL table | `reference.canonical_name` |
| Repository revision | `f657e039f0e89aa6a93cfab8a5f6dbd1970c8dae` |

## Source File

| Field | Verified value |
|---|---|
| Manifest | `database/seeds/name_catalogue/immigration/manifest.json` |
| Governed file ID | `file.novegeo.immigration.global_pairs.v001` |
| Record role | `paired_full_name_source` |
| Import enabled | True |
| Source family | `immigration_paired_names` |

## Validation Steps

The paired adapter qualification proved:

- 10 source rows sampled;
- 20 candidates produced;
- exactly one `first_name` and one `surname` per source row;
- shared `source_record_id` within each pair;
- matching `component_role`;
- correct external-record suffixes:
  - `:first`
  - `:surname`
- simulation runtime preserved;
- no database connection or write during adapter qualification.

The reusable qualifier was extended with a `paired_mode` that supports:

- two candidates per source row;
- expected candidate count of `sample_size * 2`;
- actual read-back kind per candidate;
- source-family verification for `immigration_paired_names`;
- candidate-level pair evidence maps;
- semantic collision handling for already-existing canonical identities.

## Qualification Execution

### First bounded run

| Check | Result |
|---|---:|
| Batch ID | `namebatch:fa9cd38c21a14adb929cbc6b` |
| Candidates | 20 |
| Approved | True |
| Imported | 19 |
| Already existed | 1 |
| Failed | 0 |
| Complete | True |
| Count before | 70 |
| Count after | 89 |
| Count delta | 19 |

The first run exposed one valid semantic collision:

```text
Lorenzo
name kind: first_name
runtime: simulation
```

Source record `3` created the canonical row. Source record `6` later resolved to the same canonical identity.

This behavior was correct because canonical identity is based on:

```text
runtime_mode + name_kind + normalized search value
```

The qualifier was corrected so an `already_exists` outcome verifies canonical semantic identity without requiring the existing row to replace its original source provenance.

## Idempotent Verification

The corrected qualifier was rerun against the same governed batch.

| Check | Result |
|---|---:|
| Imported | 0 |
| Already existed | 20 |
| Failed | 0 |
| Complete | True |
| Count before | 89 |
| Count after | 89 |
| Count delta | 0 |
| Stored or resolved | 20 |

The rerun proved:

- all 20 candidate components resolve successfully;
- no duplicate canonical rows are created;
- canonical IDs remain stable;
- the `Lorenzo` semantic reuse remains correctly resolved.

## PostgreSQL Read-back Verification

A read-only display qualification reconstructed every pair from the governed source and resolved both candidate components against PostgreSQL.

### Verified Pairs

| Pair | First name | Surname | Source record | Semantic reuse |
|---:|---|---|---:|---|
| 1 | Ibrahim | Du Monceau | 1 | No |
| 2 | Daniel | García Hernández | 2 | No |
| 3 | Lorenzo | Rodríguez Cruz | 3 | No |
| 4 | Hamza | Smith-Jones | 4 | No |
| 5 | Andrea | Van der Berg | 5 | No |
| 6 | Lorenzo | De Mornay | 6 | First name reused |
| 7 | Tariq | De Vito | 7 | No |
| 8 | Diego | Del Largo | 8 | No |
| 9 | Jaco | Von Richthofen | 9 | No |
| 10 | Edoardo | Von Kleist | 10 | No |

### Shared Canonical Identity

The first-name component for pair 6 resolved as:

```text
Canonical value: Lorenzo
Requested source record: 6
Stored provenance source record: 3
Semantic identity reused: True
Canonical ID: name:8c364ba79587d1c30a5a6dfc
```

This is expected canonical deduplication, not corruption.

## Display Verification Result

```text
IMMIGRATION PAIRED-NAME DISPLAY VERIFICATION: PASSED
Displayed governed pairs: 10
Resolved candidate components: 20
Unique canonical identities: 19
Cross-source semantic identity reuses: 1
Expected shared identity: Lorenzo
Final canonical-name database count: 89
Database writes performed: 0
```

## Evidence Summary

| Evidence | Result |
|---|---|
| Governed source contract | Passed |
| Paired adapter shape | Passed |
| 10 source rows | Verified |
| 20 candidate components | Verified |
| 10 first names | Verified |
| 10 surnames | Verified |
| Shared source record within each pair | Passed |
| Component-role integrity | Passed |
| PostgreSQL import | Passed |
| First-run semantic collision handling | Correct |
| Idempotent rerun | Passed |
| Duplicate creation | 0 |
| Pair display verification | Passed |
| Unique canonical identities | 19 |
| Cross-source semantic reuse | 1 |
| Final canonical-name count | 89 |

## Production Readiness Decision

**PASSED for bounded governed simulation import.**

The Immigration Paired Names path is qualified for the current bounded simulation workflow.

The result also establishes an important architectural boundary:

```text
Canonical Name Registry
is not the same as
Immigration Source Relationship Ledger
```

The current canonical-name table preserves one canonical semantic identity and the provenance of the row that first created it. It does not preserve every later source-row relationship that resolves to the same canonical name.

## Lessons Learned

1. One governed source row can produce multiple canonical-name candidates.
2. Pair integrity must be verified before import and again during read-back.
3. Canonical deduplication can reduce the final row count below the candidate count.
4. `already_exists` is a successful semantic resolution, not a failure.
5. Existing canonical provenance should not be overwritten by later duplicate source rows.
6. A separate durable relationship or import-receipt ledger is needed to preserve every source-row-to-canonical-name association.
7. The expected final canonical-name total for this qualification is `89`, not `90`, because `Lorenzo` is shared across two immigration pairs.

## Final M008 Qualification Status

```text
✅ Native First Names
✅ Native Middle Names
✅ Native Surnames
✅ Multicultural First Names
✅ Multicultural Accented First Names
✅ Multicultural Family Names
✅ Multicultural Accented Family Names
✅ Immigration Paired Names
```

## Final Qualified Canonical-Name Baseline

```text
first_name     simulation     39
middle_name    simulation     10
surname        simulation     40
---------------------------------
TOTAL                         89
```

## Next Milestone

Design and qualify the durable source-component relationship ledger for cases where multiple governed source rows resolve to one canonical identity.
