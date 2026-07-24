# Nexa Provider Platform
## M008 — Master Registry Foundation
### Phase A Engineering Research

**Repository basis:** uploaded snapshot `nexa-provider-platform-main (12).zip`

**Review posture:** current repository first; M001–M007 are referenced only where M008 consumes their proven interfaces or conventions. No production code or roadmap status was changed by this package.

# 01 — Upstream Dependency Map

## 1. Purpose

This map identifies only the already-built components that M008 must consume or remain compatible with. It is not a re-audit of M001–M007. The dependency test is practical: a prior package appears here only where current M008 code, documents, or planned child milestones require it.

## 2. Current baseline

- Python files inspected: **247**
- Markdown files inspected: **34**
- Empty files/placeholders: **74**
- Compilation baseline: **passed**
- Test baseline: **................................................................... [ 85%] ............................................................... [ 91%] ............................................................. [ 96%] ................................                                   [100%] 1050 passed, 356 subtests passed in 0.77s**

## 3. Direct dependency map

| Existing foundation | Evidence in repository | M008 consumption | Boundary |
|---|---|---|---|
| Core contracts | `shared/contracts/`, contract-related tests, architecture API rules | Contract shape, validation/result conventions, immutable request/response boundaries | M008 must not invent a parallel contract language |
| Shared kernel/runtime | `shared/runtime/`, `shared/config/`, NPP-012 | Runtime-mode metadata and environment-safe behaviour | Registry domain objects must not hard-code a deployment mode |
| Storage foundation | `shared/storage/`, `storage/`, NPP-004 and NPP-014 | Storage independence, local-first persistence expectations | Core registry models cannot import JSON, CSV, Supabase, or filesystem adapters |
| Repository foundation | `shared/repositories/` and repository unit/integration tests | Repository interfaces, result/error/factory/registry patterns | `registries/ports/*` must align rather than duplicate |
| Event infrastructure | `shared/events/` and `tests/unit/events/` | Immutable event envelopes, metadata, repository and engine conventions | M008.10 must extend the event system, not create a registry-only bus |
| Audit infrastructure | `shared/audit/` and `tests/shared/audit/` | Actor/source metadata, audit records, query/export/integrity/API contracts | `registry_audit_port.py` must adapt to M007, not replace it |
| Roadmap package | `roadmap/`, `roadmap_data.py`, `roadmap_frontend.py`, `ROADMAP.md` | Stable record IDs, validation, generation, progress and evidence | Structural mutation is not yet exposed as an implemented command |

## 4. Existing registry dependencies

The implemented `registries/core` and `registries/validators` files currently import only Python standard-library modules and other registry modules. They do **not** yet import `shared.repositories`, `shared.events`, or `shared.audit`. This confirms that the present code is mostly domain-model and validation work, not an integrated M008 subsystem.

## 5. Dependency rules locked for M008

1. M008 may depend on prior public interfaces; it must not rewrite validated prior packages merely for style.
2. Integration files in earlier packages require explicit approval and versioned delivery.
3. Registry domain objects remain storage and transport independent.
4. Events and audit are separate concerns: a domain event records a business fact; audit records attempted and completed activity, including rejected access where policy requires it.
5. Runtime mode, actor, source, correlation and idempotency metadata must be carried through approved shared contracts rather than embedded ad hoc.
6. M008 tests append to the repository test body; earlier tests remain untouched.

## 6. Roadmap insertion/renumbering finding

The roadmap model explicitly states that visible milestone numbers are positional and `record_id` is stable across renumbering. However, repository inspection found no callable insertion or renumbering function in `roadmap/`, `roadmap.py`, or `roadmap_frontend.py`. The current package supports modelling, validation, querying, generation, verification, progress and history—not structural mutation. Therefore automatic insertion/renumbering is an architectural capability implied by stable IDs, but **not yet a tested operational feature**. It must not be relied upon until a dedicated mutation API and tests exist.

## 7. Conclusion

M008 can begin from the current repository without reopening M001–M007. Its critical work is integration discipline: use the existing repository, event and audit systems at their public boundaries while preserving the registry core's current domain independence.
