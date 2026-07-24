# Nexa Provider Platform
## M008 — Master Registry Foundation
### Phase A Engineering Research

**Repository basis:** uploaded snapshot `nexa-provider-platform-main (12).zip`

**Review posture:** current repository first; M001–M007 are referenced only where M008 consumes their proven interfaces or conventions. No production code or roadmap status was changed by this package.

# 06 — Integration Boundaries

## 1. Allowed direct dependencies

| M008 area | Allowed dependency | Reason |
|---|---|---|
| core models | Python stdlib and registry value types | preserve domain purity |
| validators | registry core models and validation value types | deterministic stateless validation |
| repository ports | approved shared repository contracts/types | consistency with M005 |
| memory repository | registry ports plus shared repository primitives | testable local adapter |
| events | shared event contracts/engine/repositories | consistency with M006 |
| audit integration | shared audit public API/contracts | consistency with M007 |
| APIs | registry services/contracts and shared contract conventions | transport-neutral application boundary |
| catalogues/factory | definitions, ports and configuration contracts | controlled discovery/construction |

## 2. Disallowed or deferred dependencies

M008 must not directly depend on:

- concrete national identity, SIM, telecom, banking, business or employee domains;
- HTTP frameworks or public network endpoints;
- Supabase/database adapters before the relevant persistence milestone;
- unfinished sync packages;
- NexaPOS implementation code;
- external government, telecom or financial APIs;
- frontend click tracking implementations.

## 3. Files from earlier parent milestones

Earlier files remain read-only references unless an integration defect makes a versioned update critical. Any such update requires:

1. explicit authorization;
2. old tests retained;
3. new regression tests appended;
4. versioned filename in the delivery ZIP;
5. placement mapping to the original repository path.

## 4. Document authority

For M008, the most direct governing documents are MR-001 through MR-012, supported by NPP-001, NPP-004 through NPP-009, NPP-011 through NPP-014. Where documents conflict or leave a gap, the gap must be recorded; implementation must not silently invent policy.

## 5. Roadmap structural boundary

Roadmap rebuilding is allowed only when a critical architectural gap cannot be represented by M008.1–M008.14. Because automatic mutation is not currently implemented/tested, any structural change first requires a roadmap-mutation mini-project or a controlled manual transformation with exhaustive validation and diff review.

## 6. Public API boundary

The root `registries/__init__.py` remains empty. A stable public package surface should be locked only after contracts, base registry, repository, catalogue, lifecycle and validation interfaces are known. Premature exports would make later refactoring a breaking change.
