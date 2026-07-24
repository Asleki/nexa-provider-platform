# Nexa Provider Platform
## M008 — Master Registry Foundation
### Phase A Engineering Research

**Repository basis:** uploaded snapshot `nexa-provider-platform-main (12).zip`

**Review posture:** current repository first; M001–M007 are referenced only where M008 consumes their proven interfaces or conventions. No production code or roadmap status was changed by this package.

# 04 — Responsibility Matrix

## 1. Ownership matrix

| Responsibility | Primary owner in M008 | Existing repository evidence | Must not be owned by |
|---|---|---|---|
| Registry definition metadata | M008.1/M008.3 | `registries/core/registry_definition.py` | repositories, adapters |
| Namespace and identifier definitions | M008.2 | core definition files | API transport |
| Concrete identifier reference | M008.2 | `identifier_reference.py` | sequence generator alone |
| Identifier generation policy | M008.2 plus later domain registries | `numbering_strategy.py`, MR-007 | generic repository |
| Repository contract | M008.4 | empty registry ports plus `shared/repositories` | base registry implementation |
| In-memory persistence | M008.5 | no registry implementation yet | core models |
| Controlled construction | M008.6 | no factory yet | catalogue |
| Discovery/registration of definitions | M008.7 | empty catalogue placeholders | record repository |
| Lifecycle transitions | M008.8 | enum exists; policy placeholder empty; MR-005 | arbitrary callers |
| Validation | M008.9 | validator package exists | repository adapters |
| Registry domain events | M008.10 | M006 event infrastructure | audit subsystem |
| Application-facing API contracts | M008.11 | NPP-008; no registry API package yet | HTTP framework |
| Audit adaptation | M008.12 | M007 infrastructure; empty port | registry domain event bus |
| Test ownership | M008.13 | no dedicated registry tests | production modules |
| Export/public API and hardening | M008.14 | partial core/validator exports | individual leaf modules alone |

## 2. Cross-cutting metadata

| Metadata | Source of truth | Registry responsibility |
|---|---|---|
| Stable record identity | registry identifier model | validate and preserve |
| Actor/source | M007 audit contracts | pass through operation context |
| Correlation/idempotency | shared contracts/events/API conventions | preserve across operation boundaries |
| Runtime mode | shared runtime | isolate simulation/test/production behaviour |
| Timestamp | shared event/audit policy | use approved clock/metadata conventions |
| Version | each definition/event/API contract | explicit and immutable where required |

## 3. Anti-god-object rule

The future Base Registry may coordinate, but it must delegate persistence, validation, lifecycle policy, event creation and audit recording. It should not directly serialize files, open databases, generate domain-specific IDs, or interpret user-interface clicks.

## 4. Traceability classification

| Activity | Domain event? | Audit/security activity? | Notes |
|---|---|---|---|
| Registry entry successfully registered | Yes | Yes | state change and attributable action |
| Duplicate registration rejected | Usually rejection event or result | Yes | exact event policy to be locked in M008.10 |
| Read/lookup | Not always | Yes when sensitive, denied, or policy-controlled | avoid flooding domain event stream |
| Open page/click/refresh | No registry domain event by default | UI/access telemetry | future interface layer concern |
| Lifecycle transition | Yes | Yes | transition reason and actor required |
| Repository retry | No business event | operational audit/metrics | infrastructure concern |

## 5. Decision

M008 should be organized as collaborating components, not one universal registry class. The repository structure already supports this and should be preserved.
