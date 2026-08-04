# PWA-003 — Foundation Verification and Operating Rules

## Document control

| Field | Value |
|---|---|
| Document ID | `PWA-003` |
| Parent foundation | `P001 — NexiLabs PWA Project Foundation` |
| Status | Normative foundation |

## Purpose

This document defines how the PWA foundation is verified and how future
milestones are accepted, packaged, completed, and locked.

It replaces several tiny roadmap items for roadmap files, CLI checks, generated
Markdown, and foundation tests with one operating standard.

## Foundation verification

The PWA roadmap foundation is healthy when:

```bash
python pwa_roadmap.py verify
python pwa_roadmap_frontend.py --check
```

both pass and the generated roadmap matches the canonical dataset.

The Python governance files must compile:

```bash
PYTHONPATH=. python -m compileall -q   pwa_roadmap.py   pwa_roadmap_data.py   pwa_roadmap_frontend.py
```

## Functional milestone acceptance

A later engineering milestone is complete only when:

1. it introduces a real production capability;
2. its production files compile or build;
3. matching tests verify observable behaviour;
4. isolated tests pass;
5. active-package regression passes;
6. full repository regression passes;
7. documentation is updated where necessary;
8. roadmap status is changed only after validation;
9. generated roadmap output is refreshed;
10. implementation and roadmap update are committed together.

## Test rule

Tests must validate contracts or behaviour introduced by production code.

A test that only searches a Markdown document for expected words is not enough
to justify a standalone engineering milestone.

Documentation may still receive structural checks as part of a wider foundation
or release test, but documentation existence alone is not a PWA capability.

## Delivery rule

Functional milestone ZIPs should contain:

```text
P00X.X_Milestone_Name/
├── new-production-files/
├── new-test-files/
├── versioned-updated-files/
├── PLACEMENT_GUIDE.txt
├── IMPLEMENTATION_SUMMARY.txt
├── REFERENCE_FILES.txt
├── TEST_COMMANDS.txt
├── TEST_RESULTS.txt
└── CHANGELOG.txt
```

A documentation consolidation package may instead contain the exact canonical
documents plus a reviewed roadmap-data replacement.

## Immutability rule

After implementation, tests, documentation, review, merge, and push:

- no feature additions to the locked milestone;
- no unplanned refactoring;
- no API redesign;
- no renaming that changes semantic identity;
- no architectural rewrite.

New functionality must arrive through later modules, services, adapters,
registries, events, migrations, APIs, or frontend features.

## Security checks reserved for executable milestones

Later application milestones must progressively verify:

- no database credentials in browser bundles;
- no direct PostgreSQL or RDS endpoints;
- HTTPS-only production API bases;
- explicit runtime mode;
- service-worker cache boundaries;
- safe offline data handling;
- secure headers;
- versioned API contracts;
- authorized response shaping.

## Roadmap restructuring rule

When an early roadmap contains excessive administrative fragmentation:

1. preserve completed factual work;
2. consolidate documentation into a small foundation set;
3. remove redundant planned items;
4. replace them with capability-oriented milestones;
5. regenerate the roadmap;
6. run roadmap verification;
7. review the diff before commit.

## Locked outcome

The PWA project uses a small documentation foundation and a capability-oriented
engineering roadmap. Tests prove executable behaviour, roadmap status follows
validation, and completed work becomes immutable after merge.
