# M008.15 — Multicultural Family Names Qualification Journey

## Objective

Qualify the governed import of the first ten Multicultural Family Names into the NPP PostgreSQL canonical-name registry and prove:

- correct `surname` mapping;
- simulation-runtime isolation;
- preservation of multicultural source metadata;
- absence of native tribe references;
- successful PostgreSQL persistence and read-back;
- idempotent rerun behavior;
- zero duplicate creation.

## Dataset Information

| Field | Verified value |
|---|---|
| Dataset ID | `dataset.novegeo.name_catalogue.multicultural.v001` |
| Source family | `multicultural_atomic` |
| Runtime mode | `simulation` |
| Target name kind | `surname` |
| Qualification sample size | `10` |
| Database | `npp_dev` |
| PostgreSQL schema | `reference` |
| PostgreSQL table | `reference.canonical_name` |
| Repository revision | `caed8eda15e3af727cbc83ffecf0598b7876cd96` |

## Source File

| Field | Verified value |
|---|---|
| Governed file ID | `file.novegeo.multicultural.family_names.v001` |
| Manifest | `database/seeds/name_catalogue/multicultural/manifest.json` |
| Source role | Multicultural atomic family-name source |
| Target kind | `surname` |
| Expected reference state | `unresolved` |
| Expected culture references | empty |

## Validation Steps

The reusable name qualifier was corrected before this qualification so that native-surname rules applied only when:

```text
manifest.source_family = novegeo_native
and
target_kind = surname
```

This prevented Multicultural Family Names from being incorrectly required to carry native NoveGeo tribe references.

The qualification then verified the following candidate rules:

- `name_kind = surname`;
- `runtime_mode = simulation`;
- `source_family = multicultural_atomic`;
- `origin_label` is present;
- `language_label` is present;
- `reference_state = unresolved`;
- `culture_refs = []`;
- batch approval succeeds;
- no candidate warnings are present.

The same metadata rules were verified again after PostgreSQL read-back.

## Qualification Execution

### First bounded run

| Check | Result |
|---|---:|
| Batch ID | `namebatch:57cb6f18abf03624dffc452a` |
| Candidates | 10 |
| Approved | True |
| Imported | 10 |
| Already existed | 0 |
| Failed | 0 |
| Complete | True |
| Count before | 50 |
| Count after | 60 |
| Count delta | 10 |
| Read-back verified | 10/10 |

Qualification result:

```text
BOUNDED NAME IMPORT QUALIFICATION: PASSED
Stored or resolved: 10
Imported now: 10
Previously existing: 0
Database count delta: 10
Final canonical-name count: 60
Target kind: surname
Runtime: simulation
Database: npp_dev
```

## Idempotent Verification

The exact same governed batch was executed again.

| Check | Result |
|---|---:|
| Imported | 0 |
| Already existed | 10 |
| Failed | 0 |
| Complete | True |
| Count before | 60 |
| Count after | 60 |
| Count delta | 0 |
| Read-back verified | 10/10 |

This proved:

- duplicate detection is functioning;
- repeated execution creates no duplicate rows;
- existing canonical IDs resolve correctly;
- the same semantic surname identities remain stable;
- the database remains unchanged on rerun.

## PostgreSQL Read-back Verification

A direct, read-only query was executed against:

```text
reference.canonical_name
```

The query filtered by:

- dataset ID;
- source file ID;
- `runtime_mode = simulation`;
- `name_kind = surname`.

The display verification confirmed all ten expected rows and performed zero writes.

## Verified Stored Names

| # | Canonical value | Search value | Origin | Language | Reference state | Culture refs |
|---:|---|---|---|---|---|---|
| 1 | Smith | smith | British Isles | English | unresolved | `[]` |
| 2 | Jones | jones | British Isles | English | unresolved | `[]` |
| 3 | Taylor | taylor | British Isles | English | unresolved | `[]` |
| 4 | Brown | brown | British Isles | English | unresolved | `[]` |
| 5 | Wilson | wilson | British Isles | English | unresolved | `[]` |
| 6 | Johnson | johnson | British Isles | English | unresolved | `[]` |
| 7 | Davies | davies | British Isles | English | unresolved | `[]` |
| 8 | Robinson | robinson | British Isles | English | unresolved | `[]` |
| 9 | Wright | wright | British Isles | English | unresolved | `[]` |
| 10 | Thompson | thompson | British Isles | English | unresolved | `[]` |

Display result:

```text
MULTICULTURAL FAMILY-NAME DISPLAY VERIFICATION: PASSED
Displayed records: 10
Database writes performed: 0
```

## Evidence Summary

| Evidence | Result |
|---|---|
| Governed source contract selected | Passed |
| Candidate validation | Passed |
| Batch approval | Passed |
| PostgreSQL import | Passed |
| Runtime isolation | Passed |
| `surname` mapping | Passed |
| Multicultural source metadata | Preserved |
| Origin labels | Preserved |
| Language labels | Preserved |
| `reference_state = unresolved` | Preserved |
| Unexpected tribe/culture references | None |
| PostgreSQL read-back | 10/10 |
| Idempotent rerun | Passed |
| Duplicate creation | 0 |
| Final canonical-name total | 60 |

## Production Readiness Decision

**PASSED for bounded governed simulation import.**

The Multicultural Family Names source has demonstrated:

- correct source-family handling;
- stable canonical-name identity;
- correct surname semantics;
- safe idempotent re-execution;
- complete PostgreSQL persistence;
- preserved source provenance and unresolved multicultural labels.

This qualification does not by itself approve an unbounded full-catalogue production import. It qualifies the current bounded path and its controls.

## Lessons Learned

1. A shared qualifier must scope relationship rules by both source family and name kind.
2. `surname` alone is not enough to determine whether tribe references are required.
3. Native surnames and multicultural family names use different metadata contracts.
4. Multicultural atomic names correctly preserve origin and language as unresolved labels.
5. Idempotent reruns remain mandatory before a dataset is marked qualified.
6. Direct PostgreSQL display verification remains the final proof that stored values and metadata match the governed source.

## Next Dataset

**M008.16 — Multicultural Accented Family Names**

The next qualification must combine:

- multicultural origin and language metadata checks;
- `reference_state = unresolved`;
- empty `culture_refs`;
- Unicode and accent preservation;
- NFC canonical-value verification;
- NFKC plus case-fold search-value verification;
- idempotent rerun;
- PostgreSQL read-back display.
