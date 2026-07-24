# Nexa Provider Platform
## M008 — Master Registry Foundation
### Phase A Engineering Research

**Repository basis:** uploaded snapshot `nexa-provider-platform-main (12).zip`

**Review posture:** current repository first; M001–M007 are referenced only where M008 consumes their proven interfaces or conventions. No production code or roadmap status was changed by this package.

# 07 — Testing Map

## 1. Current test baseline

The uploaded snapshot compiles and passes the repository suite when executed from the repository root with `PYTHONPATH=.`:

```bash
python -m compileall -q .
PYTHONPATH=. pytest -q
```

Observed result:

```text
1050 passed, 356 subtests passed
```

A plain `pytest -q` in this review environment failed collection because the repository root was not on `sys.path`; this is an execution-environment issue, not a production failure. The delivery commands must therefore state the required root/PYTHONPATH condition unless the repository later adds test configuration.

## 2. Registry test gap

No dedicated registry test files were found under `tests/`. Existing substantial registry models, validators and errors therefore lack repository-visible milestone coverage. Compilation alone is insufficient.

## 3. Proposed test ownership by child milestone

| Child milestone | Required tests |
|---|---|
| M008.1 Contracts | construction, immutability, serialization, malformed input, public exports |
| M008.2 Identifier Model | normalization, equality, lifecycle/status semantics, format boundaries, stable identity |
| M008.3 Base Registry | coordination, delegation, no direct adapter coupling, typed outcomes |
| M008.4 Repository Interface | abstract contract conformance and result/error semantics |
| M008.5 Memory Repository | CRUD/read semantics, uniqueness, isolation, version conflicts, deterministic ordering |
| M008.6 Factory | supported/unsupported configuration, missing dependency rejection, deterministic resolution |
| M008.7 Catalogue | registration, duplicate prevention, lookup, version/capability discovery |
| M008.8 Lifecycle | complete transition matrix, invalid transition rejection, immutable history expectations |
| M008.9 Validation | all current validators plus cross-object and duplicate cases |
| M008.10 Events | envelope compatibility, metadata, serialization, event repository integration |
| M008.11 APIs | request/response contracts, errors, idempotency and transport neutrality |
| M008.12 Audit | actor/source/outcome linkage, denied attempts, integrity, no parallel audit store |
| M008.13 Tests | package integration, negative/security cases, concurrency/atomicity where applicable |
| M008.14 Stabilization | full package and repository regression, exports, docs and command reproducibility |

## 4. Append-only test rule

New tests are added beside existing tests. Existing tests may be corrected only when demonstrably defective and with explicit authorization; they must never be replaced by a narrower mini-milestone suite.

## 5. Validation ladder

For every production/test pair:

1. compile production file;
2. compile test file;
3. run isolated test file;
4. run active registry package tests;
5. after child completion, run all M008 tests;
6. run existing repository regression;
7. regenerate roadmap only after green results and approved status change.

## 6. Roadmap mutation tests required before use

A future insertion/renumbering feature requires tests for root insertion, child insertion, deep descendants, stable `record_id`, parent links, dependencies, roadmap start/end metadata, generated Markdown, history diffs, completion evidence and rollback on invalid insertion. No such mutation tests or mutation API currently exist.
