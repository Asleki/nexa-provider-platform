# =========================================================
# MR-003 — Identifier Catalogue
# =========================================================

Version: 1.0 (Draft)

Status: Draft

Architecture Family:
Master Registry Foundation

Milestone:
NPP-M006.1 — Master Registry Architecture & Identifier Catalogue

---

# 1. Purpose

The Identifier Catalogue defines every immutable identifier governed by the Master Registry Foundation.

Each identifier shall have exactly one authoritative issuing registry, one ownership domain and one lifecycle.

The Identifier Catalogue serves as the single source of truth for all identifiers recognised throughout the Nexa Provider Platform.

---

# 2. Scope

This document defines:

- Identifier families
- Identifier ownership
- Identifier purpose
- Issuing registry
- Identifier uniqueness
- Identifier immutability
- Identifier relationships
- Future identifier expansion

This document does not define numbering formats or generation algorithms. Those are specified in subsequent architecture documents.

---

# 3. Identifier Principles

Every identifier shall:

- be globally unique within its domain;
- be issued only once;
- never be reused;
- remain immutable after issuance;
- belong to exactly one authoritative registry;
- support complete lifecycle auditing;
- support future interoperability across authorised systems.

---

# 4. Core Infrastructure Identifiers

| Registry | Identifier |
|----------|------------|
| Citizen Registry | Nexa Citizen ID |
| Birth Registry | Birth Certificate Reference Number |
| National Identity Registry | National Identity Number |
| Revenue Registry | NRA PIN |
| Business Registration Registry | Business Registration Number |
| Telecom Registry | NexaCom Phone Number |
| SIM Registry | SIM Identifier (ICCID) |
| Banking Registry | Bank Account Number |
| Bank Card Registry | Bank Card Number |

---

# 5. Nexa Ecosystem Identifiers

| Registry | Identifier |
|----------|------------|
| Identity Registry | NexaID |
| Employer Registry | Employer ID |
| Employee Registry | Employee ID |
| Device Registry | Nexa Device ID |
| NexaPesa Merchant Registry | Merchant Number |
| NexaPesa Merchant Registry | Till Number |

---

# 6. Shared Infrastructure Identifiers

Shared Infrastructure Registries may introduce additional identifiers for internal platform operation.

Examples include:

- Audit Record ID
- Notification ID
- Certificate ID
- Cryptographic Key ID
- Configuration ID
- Time Reference ID

These identifiers support platform infrastructure rather than representing people, businesses or operational entities.

---

# 7. Identifier Ownership

Each identifier shall be owned by exactly one registry.

Ownership includes:

- identifier issuance;
- uniqueness validation;
- lifecycle management;
- revocation where applicable;
- audit history;
- verification services.

No other registry may issue or modify another registry's identifier.

---

# 8. Identifier Relationships

Identifiers may reference one another without transferring ownership.

Examples include:

- Employee ID references Employer ID.
- NexaID references Nexa Citizen ID.
- Bank Card Number references Bank Account Number.
- SIM Identifier references NexaCom Phone Number.
- Merchant Number references Business Registration Number.

References establish relationships only and shall never imply ownership transfer between registries.

---

# 9. Future Identifier Expansion

New identifiers may be introduced provided they:

- belong to an approved registry;
- remain globally unique within their domain;
- conform to MR-001;
- are added to this Identifier Catalogue before implementation.

---

End of MR-003 (Version 1.0 Draft)