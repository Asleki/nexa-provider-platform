# M008.12 — Native Surnames Qualification Journey

This document records only verified evidence from the bounded Native Surnames qualification against the Nexa Provider Platform development PostgreSQL database.

## Objective

Qualify the governed NoveGeo native surname source through the real repository-to-PostgreSQL path and prove that:

- governed surname rows can be adapted into approved `surname` candidates;
- candidates can be stored in `reference.canonical_name` under `simulation` runtime;
- every stored surname preserves its source provenance;
- every stored surname preserves exactly one governed tribe reference in `culture_refs`;
- `attributes.seed.tribe_reference_state` remains `seed_reference_reserved`;
- rerunning the same bounded batch is idempotent;
- the real stored names and metadata can be read back directly from PostgreSQL.

## Dataset Information

| Field | Verified value |
|---|---|
| Milestone | M008.12 |
| Dataset ID | `dataset.novegeo.name_catalogue.native.v001` |
| Dataset family | `novegeo_native` |
| Runtime | `simulation` |
| Environment | `development` |
| Database | `npp_dev` |
| PostgreSQL schema | `reference` |
| PostgreSQL table | `canonical_name` |
| Repository revision | `21eba1b37f1ea81c7f78599031f49f2c6bf1a94d` |
| Bounded sample size | 10 |

## Source File

| Field | Verified value |
|---|---|
| Manifest | `database/seeds/name_catalogue/novegeo/manifest.json` |
| Governed file ID | `file.novegeo.native.surnames.v001` |
| Target name kind | `surname` |
| Supporting reference role | `supporting_reference` |
| Governed tribe references loaded | 10 |
| Explicit confirmation | `IMPORT 10 SURNAMES` |

## Validation Steps

The qualification followed the established verification path:

1. Restored the controlled environment variables for the development database.
2. Confirmed the repository revision used for the run.
3. Confirmed the current PostgreSQL baseline.
4. Verified `surname` count was zero before the first run.
5. Extended the reusable temporary qualifier to load governed tribe IDs through `load_tribe_ids`.
6. Required exactly one supporting-reference source for the native dataset.
7. Required exactly 10 governed NoveGeo tribe references.
8. Required every surname candidate to contain exactly one `culture_ref`.
9. Required the candidate tribe reference to exist in the governed tribe set.
10. Required `tribe_reference_state = seed_reference_reserved` before persistence.
11. Required the same tribe reference and metadata after PostgreSQL read-back.
12. Compiled the qualifier successfully before execution.

## Qualification Execution

### Baseline before import

```text
first_name           simulation      10
middle_name          simulation      10
surname              simulation       0
Total                                 20
```

### First bounded import result

| Check | Result |
|---|---:|
| Batch ID | `namebatch:145b582aa5a5b59604a3ba4f` |
| Candidates | 10 |
| Approved | True |
| Imported | 10 |
| Already existed | 0 |
| Failed | 0 |
| Complete | True |
| Count before | 20 |
| Count after | 30 |
| Count delta | 10 |
| Item read-back | 10/10 |

The first bounded run passed with no failures and produced ten new canonical surname rows.

## Idempotent Verification

The exact same qualifier was run again against the same governed source, runtime and batch identity.

| Check | Result |
|---|---:|
| Imported | 0 |
| Already existed | 10 |
| Failed | 0 |
| Complete | True |
| Count before | 30 |
| Count after | 30 |
| Count delta | 0 |
| Item read-back | 10/10 |

This proves:

- duplicate detection is functioning;
- the same governed batch can be safely retried;
- no duplicate canonical surname rows are created;
- existing canonical IDs are resolved on rerun;
- the `surname` semantic identity remains stable;
- runtime separation remains `simulation`;
- tribe-reference safeguards continue to pass during idempotent resolution.

## PostgreSQL Read-back Verification

A direct read-only query inspected the stored rows in:

```text
reference.canonical_name
```

The query verified these fields for every row:

- `name_id`
- `canonical_value`
- `search_value`
- `name_kind`
- `status`
- `runtime_mode`
- `created_at`
- `source_reference`
- `culture_refs`
- `attributes.seed.file_id`
- `attributes.seed.source_record_id`
- `attributes.seed.source_family`
- `attributes.seed.tribe_reference_state`

The display verification ended with:

```text
NATIVE SURNAME DISPLAY VERIFICATION: PASSED
Displayed records: 10
Database writes performed: 0
```

## Verified Stored Names

| Source record | Canonical surname | Canonical name ID | Culture refs | Tribe reference state |
|---|---|---|---|---|
| `sn_001` | Bregach | `name:8aaa7276cc05abf290656069` | `trb_001` | `seed_reference_reserved` |
| `sn_002` | Bregar | `name:e81394622c80aaa01e054819` | `trb_001` | `seed_reference_reserved` |
| `sn_003` | Bregath | `name:bb78e6dd2b05f9db7c04db6f` | `trb_001` | `seed_reference_reserved` |
| `sn_004` | Bregax | `name:c48caa54e803df41b293f070` | `trb_001` | `seed_reference_reserved` |
| `sn_005` | Bregburg | `name:7d3e011279cfd92250fc98a4` | `trb_001` | `seed_reference_reserved` |
| `sn_006` | Bregen | `name:c9ec0e7cb4c36f72c4679aba` | `trb_001` | `seed_reference_reserved` |
| `sn_007` | Breger | `name:058bc79dc6f6fd60ba22f27f` | `trb_001` | `seed_reference_reserved` |
| `sn_008` | Bregic | `name:b969ff1dc54aa3a34f109b79` | `trb_001` | `seed_reference_reserved` |
| `sn_009` | Bregoff | `name:5b611bfa9b7e1316c852e60e` | `trb_001` | `seed_reference_reserved` |
| `sn_010` | Bregog | `name:13ed366f165624f2510e16e9` | `trb_001` | `seed_reference_reserved` |

All ten rows were verified as:

- `name_kind = surname`;
- `status = active`;
- `runtime_mode = simulation`;
- `source_reference = dataset.novegeo.name_catalogue.native.v001`;
- `source file = file.novegeo.native.surnames.v001`;
- `source family = novegeo_native`;
- exactly one `culture_ref`;
- `culture_refs[0] = trb_001` for this bounded sample;
- `tribe_reference_state = seed_reference_reserved`.

## Evidence Summary

```text
Governed source validation          PASSED
Candidate kind validation           PASSED
Runtime validation                  PASSED
Tribe reference loading             PASSED
Candidate culture_refs validation   PASSED
Candidate tribe-state validation    PASSED
Controlled import                   PASSED
PostgreSQL persistence              PASSED
Immediate read-back                 PASSED
Stored culture_refs validation      PASSED
Stored tribe-state validation       PASSED
Idempotent rerun                    PASSED
Direct PostgreSQL display           PASSED
Database writes during display      0
```

### Current database baseline

```text
first_name    simulation    10
middle_name   simulation    10
surname       simulation    10
Total                       30
```

## Production Readiness Decision

**Decision: Native Surnames bounded qualification passed.**

The existing Name Catalogue path has now demonstrated that native surnames can be validated, imported, resolved idempotently and read back with governed tribe-reference metadata intact.

This decision is limited to the bounded development qualification of ten rows in `npp_dev` under `simulation` runtime. It does not claim that the entire native surname dataset has been imported, nor that a production-runtime bulk import has been executed.

## Lessons Learned

- Surnames require more than correct `name_kind`; their governed relationship metadata must also survive persistence.
- `culture_refs` must be checked before and after the database write.
- A reserved reference value is not enough by itself; the reference must be proven to belong to the governed supporting dataset.
- `seed_reference_reserved` is important evidence that the relationship was intentionally reserved for a later authoritative registry rather than silently resolved or discarded.
- The reusable qualifier can support richer datasets when its checks are extended without changing the underlying production repository contracts.
- Idempotency must be demonstrated separately from first-write success.
- Direct PostgreSQL display remains mandatory after the importer reports success.

## Stage, Commit and Push Commands

After placing this file at:

```text
verification/0005_NATIVE_SURNAMES_QUALIFICATION_JOURNEY.md
```

run:

```bash
git status

git add verification/0005_NATIVE_SURNAMES_QUALIFICATION_JOURNEY.md

git diff --cached -- verification/0005_NATIVE_SURNAMES_QUALIFICATION_JOURNEY.md

git commit -m "docs(verification): add M008.12 Native Surnames qualification journey"

git push origin main

git status
```

Expected final state:

```text
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

## Next Dataset

```text
✅ Native First Names
✅ Native Middle Names
✅ Native Surnames
🔁 Multicultural First Names
⬜ Multicultural Accented First Names
⬜ Multicultural Family Names
⬜ Multicultural Accented Family Names
⬜ Immigration Paired Names
```

For Multicultural First Names, the next qualification must verify that unresolved origin and language references remain explicitly represented as unresolved metadata rather than being silently converted into governed references that do not yet exist.
