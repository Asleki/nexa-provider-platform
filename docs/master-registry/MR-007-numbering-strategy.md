# =========================================================
# MR-007 — Numbering Strategy
# =========================================================

Version: 1.0 (Draft)

Status: Draft

Architecture Family:
Master Registry Foundation

Milestone:
NPP-M006.1 — Master Registry Architecture & Identifier Catalogue

---

# 1. Purpose

The Numbering Strategy defines the architectural principles governing the creation, allocation and management of immutable identifiers throughout the Master Registry Foundation.

This document establishes how numbering systems remain globally unique, scalable, secure and interoperable while allowing each registry to maintain its own numbering implementation.

The Numbering Strategy defines architectural rules rather than individual numbering formats.

---

# 2. Scope

This document defines:

- Numbering principles
- Identifier uniqueness
- Namespace ownership
- Prefix allocation
- Number reservation
- Sequence management
- Future expansion
- Identifier interoperability

This document does not define the exact format of individual identifiers. Those are specified within the implementation of each registry.

---

# 3. Numbering Principles

Every identifier shall:

- be globally unique within its registry;
- be issued only once;
- never be reused;
- remain immutable after issuance;
- support future expansion;
- support long-term interoperability.

---

# 4. Registry Namespaces

Every registry shall own an independent numbering namespace.

Namespaces prevent collisions between identifiers belonging to different registries.

Examples include:

- Citizen Registry Namespace
- Birth Registry Namespace
- Business Registration Registry Namespace
- Telecom Registry Namespace
- Banking Registry Namespace
- Identity Registry Namespace

Namespaces remain independent.

No registry shall allocate identifiers within another registry's namespace.

---

# 5. Prefix Strategy

Registries may implement prefixes to improve identifier recognition.

Prefixes shall:

- identify the issuing registry;
- improve readability;
- support future expansion;
- remain stable after publication.

Prefix allocation shall be governed centrally by the Master Registry Foundation.

---

# 6. Sequence Strategy

Each registry manages its own allocation sequence.

Sequence implementation may use:

- incremental allocation;
- segmented allocation;
- distributed allocation;
- cryptographically generated identifiers;
- future approved allocation strategies.

The allocation strategy is an implementation decision and shall not affect registry ownership.

---

# 7. Reserved Number Ranges

Registries may reserve identifier ranges for specific operational purposes.

Examples include:

- testing;
- demonstrations;
- simulations;
- emergency allocations;
- future expansion.

Reserved ranges shall never overlap production allocations.

---

# 8. Identifier Length

Each registry determines the appropriate identifier length for its domain.

Identifier length should balance:

- uniqueness;
- readability;
- scalability;
- operational efficiency;
- future growth.

Length requirements may differ between registries.

---

# 9. Collision Prevention

Every issuing registry shall guarantee that duplicate identifiers cannot be created within its namespace.

Collision prevention mechanisms may include:

- sequence validation;
- uniqueness checks;
- transactional allocation;
- cryptographic randomness;
- distributed allocation safeguards.

---

# 10. Number Reuse

Identifiers shall never be reused.

Once an identifier has been allocated, it becomes permanently reserved, regardless of lifecycle state.

Retired identifiers remain permanently unavailable for future allocation.

---

# 11. Versioning

Changes to numbering implementations shall not invalidate previously issued identifiers.

Future numbering improvements shall maintain backward compatibility wherever practical.

Historical identifiers shall remain valid and verifiable.

---

# 12. Future Expansion

Future registries shall receive independent namespaces before issuing identifiers.

The introduction of new registries shall not require renumbering existing identifiers.

The Numbering Strategy shall remain scalable to support future expansion of the Nexa Provider Platform.

---

End of MR-007 (Version 1.0 Draft)