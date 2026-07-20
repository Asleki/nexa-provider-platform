# =========================================================
# MR-004 — Registry Ownership & Issuance Matrix
# =========================================================

Version: 1.0 (Draft)

Status: Draft

Architecture Family:
Master Registry Foundation

Milestone:
NPP-M006.1 — Master Registry Architecture & Identifier Catalogue

---

# 1. Purpose

The Registry Ownership & Issuance Matrix defines ownership authority for every immutable identifier governed by the Master Registry Foundation.

It specifies which registry is authorised to issue an identifier, which systems may request it, which systems may validate it, and which systems may only reference it.

This document establishes the governance model that prevents duplicate issuance, conflicting ownership and unauthorised identifier creation.

---

# 2. Scope

This document defines:

- Registry ownership
- Issuing authority
- Validation authority
- Referencing authority
- Identifier request authority
- Ownership restrictions
- Governance rules

---

# 3. Registry Governance Principles

Every immutable identifier shall have:

- one issuing registry;
- one authoritative owner;
- one lifecycle owner;
- one verification authority.

No business application, service or registry may issue another registry's identifier.

---

# 4. Ownership Matrix

| Registry | Identifier | Issues | Validates | References |
|----------|------------|--------|-----------|------------|
| Citizen Registry | Nexa Citizen ID | ✓ | ✓ | ✓ |
| Birth Registry | Birth Certificate Reference Number | ✓ | ✓ | ✓ |
| National Identity Registry | National Identity Number | ✓ | ✓ | ✓ |
| Revenue Registry | NRA PIN | ✓ | ✓ | ✓ |
| Business Registration Registry | Business Registration Number | ✓ | ✓ | ✓ |
| Telecom Registry | NexaCom Phone Number | ✓ | ✓ | ✓ |
| SIM Registry | SIM Identifier | ✓ | ✓ | ✓ |
| Banking Registry | Bank Account Number | ✓ | ✓ | ✓ |
| Bank Card Registry | Bank Card Number | ✓ | ✓ | ✓ |
| Employer Registry | Employer ID | ✓ | ✓ | ✓ |
| Employee Registry | Employee ID | ✓ | ✓ | ✓ |
| Device Registry | Nexa Device ID | ✓ | ✓ | ✓ |
| NexaPesa Merchant Registry | Merchant Number | ✓ | ✓ | ✓ |
| NexaPesa Merchant Registry | Till Number | ✓ | ✓ | ✓ |
| Identity Registry | NexaID | ✓ | ✓ | ✓ |

---

# 5. Consumer Responsibilities

Business applications may:

- request identifiers;
- verify identifiers;
- reference identifiers;
- display identifiers where authorised.

Business applications shall not:

- generate identifiers;
- modify identifiers;
- duplicate identifiers;
- transfer identifier ownership.

---

# 6. Collaborative Issuance

Some identifiers require collaborative issuance.

The first implementation of collaborative issuance is NexaID.

NexaID shall be minted through the controlled cooperation of authorised systems under the governance of the Identity Registry.

The Identity Registry remains the sole authoritative owner of NexaID.

---

# 7. Ownership Restrictions

Registries shall not:

- issue another registry's identifiers;
- modify another registry's records;
- assume ownership of external identifiers;
- bypass registry governance.

---

# 8. Future Expansion

Future registries shall be added to this ownership matrix before implementation begins.

Every new registry shall define:

- issuing authority;
- validation authority;
- referencing authority;
- ownership boundaries.

---

End of MR-004 (Version 1.0 Draft)