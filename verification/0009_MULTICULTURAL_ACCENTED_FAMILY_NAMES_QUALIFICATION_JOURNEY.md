# M008.16 — Multicultural Accented Family Names Qualification Journey

## Objective

Qualify the governed import of ten Multicultural Accented Family Names into the PostgreSQL canonical-name registry and verify Unicode preservation, multicultural metadata, idempotency, and read-back integrity.

## Dataset Information

- Dataset ID: `dataset.novegeo.name_catalogue.multicultural.v001`
- Source family: `multicultural_atomic`
- Runtime: `simulation`
- Target kind: `surname`
- Sample size: `10`
- Database: `npp_dev`
- Table: `reference.canonical_name`
- Repository revision: `a9c19a1c5d3b2d10bec0cbfb36d4795aef7fc691`

## Source File

- Manifest: `database/seeds/name_catalogue/multicultural/manifest.json`
- File ID: `file.novegeo.multicultural.accented_family_names.v001`
- Canonical Unicode rule: NFC preservation
- Search rule: NFKC plus case-fold
- Accent stripping: prohibited

## Validation Steps

The reusable qualifier was extended to recognize both accented source files:

```text
file.novegeo.multicultural.accented_first_names.v001
file.novegeo.multicultural.accented_family_names.v001
```

The qualification verified:

- `name_kind = surname`
- `runtime_mode = simulation`
- `source_family = multicultural_atomic`
- `origin_label` present
- `language_label` present
- `reference_state = unresolved`
- `culture_refs = []`
- UTF-8 round-trip integrity
- NFC canonical-value preservation
- NFKC plus case-fold search-value preservation
- non-ASCII evidence
- no accent stripping
- identical checks after PostgreSQL read-back

## Qualification Execution

### First bounded run

| Check | Result |
|---|---:|
| Batch ID | `namebatch:22571888a50820c39202df49` |
| Candidates | 10 |
| Approved | True |
| Imported | 10 |
| Already existed | 0 |
| Failed | 0 |
| Complete | True |
| Count before | 60 |
| Count after | 70 |
| Count delta | 10 |
| Read-back verified | 10/10 |

## Idempotent Verification

| Check | Result |
|---|---:|
| Imported | 0 |
| Already existed | 10 |
| Failed | 0 |
| Count before | 70 |
| Count after | 70 |
| Count delta | 0 |
| Read-back verified | 10/10 |

## PostgreSQL Read-back Verification

The direct read-only display verification passed for all ten records.

## Verified Stored Names

| # | Canonical value | Search value | Origin | Language | Reference state | Culture refs |
|---:|---|---|---|---|---|---|
| 1 | Béranger | béranger | France | French | unresolved | `[]` |
| 2 | François | françois | France | French | unresolved | `[]` |
| 3 | Clément | clément | France | French | unresolved | `[]` |
| 4 | Gagné | gagné | Canada | French | unresolved | `[]` |
| 5 | Tremblay | tremblay | Canada | French | unresolved | `[]` |
| 6 | Lévesque | lévesque | Canada | French | unresolved | `[]` |
| 7 | Müller | müller | Germany | German | unresolved | `[]` |
| 8 | Jäger | jäger | Germany | German | unresolved | `[]` |
| 9 | Schröder | schröder | Germany | German | unresolved | `[]` |
| 10 | Gómez | gómez | Spain | Spanish | unresolved | `[]` |

Verification summary:

```text
MULTICULTURAL ACCENTED FAMILY-NAME DISPLAY VERIFICATION: PASSED
Displayed records: 10
Non-ASCII names: 9
Database writes performed: 0
```

## Evidence Summary

- Governed source contract: passed
- Candidate validation: passed
- Batch approval: passed
- PostgreSQL import: passed
- Runtime isolation: passed
- Unicode NFC preservation: passed
- NFKC plus case-fold search contract: passed
- Accent stripping: not detected
- Multicultural metadata: preserved
- PostgreSQL read-back: 10/10
- Idempotent rerun: passed
- Duplicate creation: 0
- Final canonical-name count: 70

## Production Readiness Decision

**PASSED for bounded governed simulation import.**

This qualifies the controlled bounded path. It does not independently authorize an unbounded full-catalogue production import.

## Lessons Learned

1. Accented-source detection must be tied to governed file IDs.
2. Unicode validation must run before import and after read-back.
3. NFC canonical preservation and NFKC plus case-fold search normalization are separate contracts.
4. Accent stripping must fail qualification.
5. Multicultural surnames preserve unresolved origin and language labels without tribe references.
6. Idempotent reruns remain mandatory.

## Next Dataset

**M008.17 — Immigration Paired Names**
