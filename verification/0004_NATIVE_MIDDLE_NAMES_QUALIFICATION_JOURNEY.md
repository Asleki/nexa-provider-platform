# M008.11 — Native Middle Names Qualification Journey

## Objective

Qualify a bounded set of governed NoveGeo native middle names through the existing Nexa Provider Platform Name Authority path and prove that the same batch can be safely repeated without creating duplicate canonical-name records.

This qualification was limited to ten records in the development database. Its purpose was not to complete the full name catalogue import. Its purpose was to verify the current repository contracts, PostgreSQL persistence path, read-back behavior, semantic duplicate detection, runtime isolation, and reusable qualification procedure before moving to the next dataset.

## Dataset Information

| Field | Verified value |
|---|---|
| Milestone | M008.11 |
| Dataset | NoveGeo Native Name Catalogue Production Seed |
| Dataset ID | `dataset.novegeo.name_catalogue.native.v001` |
| Dataset version | `1` |
| Source family | `novegeo_native` |
| Runtime | `simulation` |
| Environment | `development` |
| Database | `npp_dev` |
| PostgreSQL schema | `reference` |
| PostgreSQL table | `reference.canonical_name` |
| Repository revision used for qualification | `e5fa7d77997f91e7655e47f7389fff0a19d3644e` |
| Sample size | `10` |
| Target name kind | `middle_name` |

## Source File

| Field | Verified value |
|---|---|
| Manifest | `database/seeds/name_catalogue/novegeo/manifest.json` |
| Governed file ID | `file.novegeo.native.second_names.v001` |
| Repository path | `database/seeds/name_catalogue/novegeo/seed_second_names.csv` |
| Record role | `atomic_name` |
| Import enabled | `true` |
| Target name kind | `middle_name` |
| Governed row count | `780` |
| SHA-256 | `d718048f49fde05668a6abc32815a639ec6058d8c010a39598223e917d6edb59` |
| Headers | `id, second_name, gender` |

## Validation Steps

The qualification followed the repository verification playbook and reused the existing production path:

```text
ProductionSeedLoader
→ ProductionSeedAdapter
→ NameCandidateValidator
→ NameImportBatch.approve()
→ ControlledNameBatchImporter
→ PostgreSQLNameRepository
→ reference.canonical_name
```

The following controls were verified before execution:

1. Repository root was `/public/nexa-provider-platform`.
2. Git branch was `main` and the working tree was clean.
3. PostgreSQL connection settings pointed to `npp_dev`.
4. TLS mode was `require`.
5. Runtime was restricted to `simulation`.
6. Environment was restricted to `development`.
7. No PostgreSQL password was stored in `PGPASSWORD`, `PGPASSFILE`, or `PGSERVICE`.
8. The manifest was loaded and validated through `ProductionSeedLoader`.
9. The selected file contract was required to be import-enabled.
10. The configured target kind had to equal the manifest target kind.
11. The source had to contain at least ten rows.
12. Each selected row had to produce exactly one candidate.
13. Each candidate had to be `middle_name` and `simulation`.
14. Candidate validation had to pass with no warnings.
15. The batch had to be approved before import.
16. The temporary qualifier had to compile successfully before execution.

## Qualification Execution

### Pre-import database baseline

Before the Native Middle Names write, PostgreSQL contained:

```text
first_name    simulation    10
middle_name   simulation     0
total                       10
```

### First bounded execution

The governed source produced an approved ten-candidate batch:

```text
Batch ID: namebatch:29967e1595201ccd2f0885fe
Candidates: 10
Approved: True
Target kind: middle_name
Runtime: simulation
```

The controlled import result was:

| Check | Result |
|---|---:|
| Imported | 10 |
| Already existed | 0 |
| Failed | 0 |
| Complete | `True` |
| Count before | 10 |
| Count after | 20 |
| Count delta | 10 |
| Immediate read-back | 10/10 |

The first bounded execution therefore passed.

## Idempotent Verification

The identical temporary qualifier was executed again using the same governed dataset, file contract, runtime, sample size, and deterministic batch identity.

The second execution returned:

| Check | Result |
|---|---:|
| Imported | 0 |
| Already existed | 10 |
| Failed | 0 |
| Complete | `True` |
| Count before | 20 |
| Count after | 20 |
| Count delta | 0 |
| Read-back verified | 10/10 |

This proves the following verified behavior for this bounded dataset:

- duplicate detection recognized all ten existing semantic identities;
- rerunning the same governed batch did not create additional rows;
- each candidate resolved to its existing canonical `name_id`;
- `middle_name` remained semantically distinct from `first_name`;
- runtime separation remained `simulation`;
- the reusable qualifier worked for a second name kind without changing production repository code.

## PostgreSQL Read-back Verification

A read-only PostgreSQL query inspected the stored records directly from:

```text
reference.canonical_name
```

The query required:

- `name_kind = 'middle_name'`;
- `runtime_mode = 'simulation'`;
- `source_reference = 'dataset.novegeo.name_catalogue.native.v001'`;
- ordering by the governed seed `source_record_id`;
- exactly ten returned records.

The display verification ended with:

```text
NATIVE MIDDLE-NAME DISPLAY VERIFICATION: PASSED
Displayed records: 10
Database writes performed: 0
```

## Verified Stored Names

| Source record ID | Canonical name | Search value | Canonical name ID | Status | Sex usage |
|---:|---|---|---|---|---|
| 1 | Alrick | `alrick` | `name:e01032dc3107fcb7241281f2` | active | male |
| 2 | Alton | `alton` | `name:5c12da0957a6ae3e75c951b3` | active | male |
| 3 | Aldan | `aldan` | `name:2909ac31acb0c4404db60d88` | active | male |
| 4 | Alborn | `alborn` | `name:9f1d6dd608e670eba9a9d16a` | active | male |
| 5 | Alfrey | `alfrey` | `name:dbe58b3aef992b58892c2b6f` | active | male |
| 6 | Aldal | `aldal` | `name:1c2736a1d22922084fa595e1` | active | male |
| 7 | Alwell | `alwell` | `name:dd2b837c40ff3a0e023a934b` | active | male |
| 8 | Almont | `almont` | `name:0effd5f705945f7c82714bbe` | active | male |
| 9 | Alford | `alford` | `name:ca000be7ff49da5fb388d8f9` | active | male |
| 10 | Alwin | `alwin` | `name:5ab3ae1d4130913d5cb2bf72` | active | male |

Every displayed row preserved:

- the canonical value;
- normalized search value;
- `middle_name` kind;
- `active` status;
- `simulation` runtime;
- source dataset reference;
- governed source file ID;
- source record ID;
- `novegeo_native` source family;
- sex-usage metadata.

## Evidence Summary

| Evidence | Verified result |
|---|---|
| Governed manifest validation | Passed |
| File contract selection | Exactly one match |
| Target-kind check | `middle_name` matched manifest |
| Runtime check | `simulation` |
| Approved bounded batch | 10 candidates |
| First controlled import | 10 imported, 0 failed |
| First count reconciliation | 10 → 20 |
| First read-back | 10/10 |
| Idempotent rerun | 0 imported, 10 existing |
| Second count reconciliation | 20 → 20 |
| Second read-back | 10/10 |
| Direct PostgreSQL display | 10 rows |
| Display operation writes | 0 |
| Final canonical-name total | 20 |

Final database baseline after qualification:

```text
first_name    simulation    10
middle_name   simulation    10
total                       20
```

## Production Readiness Decision

**Decision: Native Middle Names bounded qualification passed.**

The existing Name Authority implementation is qualified for the tested Native Middle Names path in the development database and simulation runtime.

This decision is bounded. It proves the behavior of the ten-record qualification path. It does not claim that all 780 native middle-name rows have been imported, nor that full-catalogue operational scaling has been completed.

Verified readiness includes:

- governed source loading;
- candidate adaptation;
- candidate validation;
- approval enforcement;
- controlled PostgreSQL persistence;
- semantic duplicate detection;
- idempotent rerun behavior;
- canonical-ID resolution;
- exact count reconciliation;
- record-level read-back;
- runtime isolation;
- source provenance preservation.

## Lessons Learned

1. Temporary scripts may survive a terminal restart, while shell environment variables do not. Always inspect both instead of assuming either state.
2. Re-export database and qualifier configuration after a new terminal session.
3. Compile the temporary qualifier before every execution.
4. Do not invent constructor contracts. The verified PostgreSQL construction is:

   ```text
   connection_factory
   → PostgreSQLConnectionProvider(connection_factory)
   → PostgreSQLNameRepository(provider)
   ```

5. A silent `python -m py_compile` result means the script compiled successfully.
6. Keep qualification scripts outside the repository unless a later milestone explicitly creates an approved operational CLI.
7. Verify both repository-level results and physical PostgreSQL rows.
8. Treat first execution and idempotent rerun as separate required proofs.
9. A total row count alone is insufficient; verify `name_kind`, runtime, source references, source record IDs, and metadata.
10. Preserve the distinction between a bounded qualification and a complete catalogue import.

## Stage, Commit, and Push Commands

After placing this new file at:

```text
verification/0004_NATIVE_MIDDLE_NAMES_QUALIFICATION_JOURNEY.md
```

run:

```bash
git status
```

Stage only this new verification document:

```bash
git add verification/0004_NATIVE_MIDDLE_NAMES_QUALIFICATION_JOURNEY.md
```

Inspect the staged change:

```bash
git status
```

Commit:

```bash
git commit -m "docs(verification): record native middle names qualification journey"
```

Push:

```bash
git push origin main
```

Confirm synchronization:

```bash
git status
```

Expected final repository state:

```text
On branch main
Your branch is up to date with 'origin/main'.
nothing to commit, working tree clean
```

## Next Dataset

Current qualification status:

```text
✅ Native First Names
✅ Native Middle Names
⬜ Native Surnames
⬜ Multicultural First Names
⬜ Multicultural Accented First Names
⬜ Multicultural Family Names
⬜ Multicultural Accented Family Names
⬜ Immigration Paired Names
```

The next qualification is **Native Surnames**.

Native Surnames require the same sequence:

1. validate and qualify the bounded import;
2. perform the idempotent rerun;
3. display the real stored PostgreSQL rows;
4. create the next journey document.

The additional verification focus is preservation of reserved tribe-reference metadata. The surname qualification must prove that `culture_refs`, including values such as `trb_001`, survive candidate adaptation, controlled persistence, and PostgreSQL read-back.
