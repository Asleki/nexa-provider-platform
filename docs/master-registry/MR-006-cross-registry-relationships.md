# =========================================================
# MR-006 — Cross-Registry Relationships
# =========================================================

Version: 1.0 (Draft)

Status: Draft

Architecture Family:
Master Registry Foundation

Milestone:
NPP-M006.1 — Master Registry Architecture & Identifier Catalogue

---

# 1. Purpose

This document defines how registries within the Master Registry Foundation establish, maintain and validate relationships with one another.

While every registry remains independently authoritative over its own identifiers, registries frequently require trusted references to identifiers managed by other registries.

This document defines the architectural rules governing those relationships.

---

# 2. Scope

This document defines:

- Cross-registry references
- Relationship ownership
- Relationship types
- Dependency rules
- Validation rules
- Reference integrity
- Circular dependency prevention

---

# 3. Architectural Principles

Cross-registry relationships shall:

- preserve registry independence;
- never transfer ownership;
- reference immutable identifiers only;
- remain fully auditable;
- support future expansion.

A relationship is a reference—not ownership.

---

# 4. Relationship Types

The Master Registry Foundation supports:

## 4.1 One-to-One (1:1)

One identifier references one identifier.

Examples:

- Bank Card → Bank Account
- SIM Card → Phone Number

---

## 4.2 One-to-Many (1:N)

One identifier may be referenced by many identifiers.

Examples:

- Employer → Employees
- Business Registration → Merchant Numbers

---

## 4.3 Many-to-One (N:1)

Many identifiers reference one parent identifier.

Examples:

- Multiple Devices → One Estate
- Multiple Employees → One Employer

---

## 4.4 Many-to-Many (N:N)

Relationships requiring many-to-many associations shall be implemented through dedicated relationship registries.

Direct many-to-many ownership shall not exist.

Examples include:

- Employee Skills
- Business Partnerships
- Device Sharing

---

# 5. Reference Rules

Registries may reference another registry only through its authoritative identifier.

Example:

Employee Registry

May store:

- Employer ID

May not duplicate:

- Employer details
- Employer records
- Employer ownership

---

# 6. Ownership Rules

Ownership never changes through references.

Example:

Identity Registry references Nexa Citizen ID.

Ownership remains:

Citizen Registry → Nexa Citizen ID

Identity Registry → NexaID

Neither registry owns the other's identifier.

---

# 7. Validation Rules

Before creating a relationship:

- referenced identifier must exist;
- referenced identifier must be active unless policy allows otherwise;
- issuing registry must successfully validate the reference.

Invalid references shall never be stored.

---

# 8. Circular Dependency Prevention

Registries shall not create circular ownership.

Example:

Citizen Registry

→ references NexaID

while

Identity Registry

→ requires Citizen ID

Ownership must always flow in one direction.

Circular authority is prohibited.

---

# 9. Relationship Lifecycle

Relationships possess their own lifecycle independent of identifier ownership.

Relationship states may include:

- Pending
- Active
- Suspended
- Terminated
- Archived

Changing a relationship shall never modify either identifier.

---

# 10. Future Relationship Registries

Complex relationships should be managed by dedicated registries rather than embedding relationship logic inside existing registries.

Examples include:

- Employment Relationship Registry
- Business Ownership Registry
- Account Ownership Registry
- Device Assignment Registry
- Estate Assignment Registry

---

End of MR-006 (Version 1.0 Draft)