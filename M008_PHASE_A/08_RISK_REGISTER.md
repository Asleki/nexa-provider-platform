# Nexa Provider Platform
## M008 — Master Registry Foundation
### Phase A Engineering Research

**Repository basis:** uploaded snapshot `nexa-provider-platform-main (12).zip`

**Review posture:** current repository first; M001–M007 are referenced only where M008 consumes their proven interfaces or conventions. No production code or roadmap status was changed by this package.

# 08 — Risk Register

| ID | Risk | Likelihood | Impact | Evidence | Mitigation / gate |
|---|---|---|---|---|---|
| M008-R01 | Existing registry code is treated as completed without tests | High | Critical | substantial core/validator code; no registry tests | assign every file to child milestone and test before completion |
| M008-R02 | Duplicate repository abstraction | High | Critical | empty registry ports beside mature `shared/repositories` | map and extend approved repository contracts |
| M008-R03 | Parallel audit system | Medium | Critical | empty `registry_audit_port.py` beside complete M007 | adapter/port must target M007 public API |
| M008-R04 | Parallel event system | Medium | Critical | M008.10 planned; M006 already complete | registry events use shared event contracts/engine |
| M008-R05 | God-object Base Registry | High | High | many responsibilities converge at M008.3 | enforce responsibility matrix and injected collaborators |
| M008-R06 | Lifecycle enum mistaken for lifecycle policy | High | High | enum exists, policy file empty | implement/test transition policy separately |
| M008-R07 | Domain-specific logic leaks into generic foundation | High | High | MR docs list many concrete registries | keep M008 domain-neutral; defer concrete issuance |
| M008-R08 | Error taxonomy fragmentation | Medium | High | local model errors plus `registries/errors` hierarchy | document construction vs operational errors and public mapping |
| M008-R09 | Public API locked too early | Medium | High | root package empty; partial exports only | lock exports during stabilization after interfaces settle |
| M008-R10 | Placeholder overreach | High | High | many empty adapters/governance/services | populate only by milestone ownership |
| M008-R11 | Mislabelled milestone headers create false history | High | Medium | registry files cite M006.2 while roadmap assigns M008 | versioned metadata correction after classification |
| M008-R12 | UI telemetry floods domain events | Medium | High | requirement to trace clicks/refreshes | separate domain events from access/security telemetry |
| M008-R13 | Sensitive lookups are unaudited | Medium | Critical | lookup audit policy not implemented | audit policy matrix in M008.12 |
| M008-R14 | Duplicate/uniqueness race | Medium | Critical | validators accept in-memory existing-value iterables | atomic repository uniqueness enforcement, not validator-only |
| M008-R15 | Automatic roadmap renumbering assumed to work | High | High | stable IDs documented; no mutation API/tests | do not use until implemented and tested |
| M008-R16 | Root test invocation differs by environment | Medium | Medium | `PYTHONPATH=.` required in review environment | document command or add approved pytest config later |
| M008-R17 | Sync requirements pulled into M008 prematurely | Medium | High | sync docs/packages are empty | retain sync-ready IDs/events only; defer sync implementation |
| M008-R18 | Adapters drive domain design | Medium | High | JSON/CSV/Supabase placeholders pre-exist | stabilize ports/core before adapters |
| M008-R19 | Roadmap child structure may be too coarse | Medium | High | large existing files and critical integration concerns | allow critical roadmap rebuild only after file/dependency design proves need |
| M008-R20 | Existing architecture documents conflict or are incomplete | Medium | High | multiple MR specs; empty future docs | record conflicts explicitly; no silent reconciliation |

## Risk acceptance rule

No critical risk is accepted merely because tests are green. Tests must cover the relevant risk, and architectural boundaries must also be reviewed.
