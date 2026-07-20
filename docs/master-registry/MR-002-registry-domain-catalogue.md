# =========================================================
# MR-002 — Registry Domain Catalogue
# =========================================================

Version: 1.0 (Draft)

Status: Draft

Architecture Family:
Master Registry Foundation

Milestone:
NPP-M006.1 — Master Registry Architecture & Identifier Catalogue

---

# 1. Purpose

The Registry Domain Catalogue defines every authoritative registry recognised by the Master Registry Foundation.

Each registry owns exactly one business domain and serves as the sole authority responsible for issuing, validating, managing and auditing the immutable identifiers within that domain.

To provide a scalable architecture, all registries are organised into registry families based on their operational purpose and ownership.

No two registries shall own the same identifier domain.

---

# 2. Scope

This document defines:

- Registry families
- Registry domains
- Registry responsibilities
- Registry ownership boundaries
- Registry authority
- Future registry expansion rules

This document does not define identifier formats, numbering schemes or lifecycle rules. Those are specified in later architecture documents.

---

# 3. Registry Families

The Master Registry Foundation consists of three registry families.

---

## 3.1 Core Infrastructure Registries

Core Infrastructure Registries simulate foundational public and national infrastructure upon which organisations and digital ecosystems operate.

These registries provide authoritative identities and references that may later be consumed by Nexa Ecosystem Registries.

Core Infrastructure Registries include:

- Citizen Registry
- Birth Registry
- National Identity Registry
- Revenue Registry
- Business Registration Registry
- Telecom Registry
- SIM Registry
- Banking Registry
- Bank Card Registry

---

## 3.2 Nexa Ecosystem Registries

Nexa Ecosystem Registries manage identities, assets and operational entities that exist exclusively within the Nexa Ecosystem.

These registries consume trusted information from Core Infrastructure Registries while maintaining independent ownership of Nexa operational identifiers.

Nexa Ecosystem Registries include:

- Identity Registry (NexaID)
- Employer Registry
- Employee Registry
- Device Registry
- NexaPesa Merchant Registry

Future Nexa registries may include:

- Estate Registry
- Branch Registry
- Outlet Registry
- Terminal Registry
- Operator Registry
- Loyalty Registry
- Membership Registry
- Subscription Registry
- API Client Registry
- AI Agent Registry
- Digital Asset Registry

---

## 3.3 Shared Infrastructure Registries

Shared Infrastructure Registries provide common platform services used by both Core Infrastructure Registries and Nexa Ecosystem Registries.

These registries do not represent citizens, businesses or operational entities. Instead, they provide shared platform capabilities.

Future Shared Infrastructure Registries may include:

- Audit Registry
- Configuration Registry
- Notification Registry
- Certificate Registry
- Cryptographic Key Registry
- Time Registry

---

# 4. Registry Domains

The initial registry domains are defined below.

---

## 4.1 Citizen Registry

Registry Family:
Core Infrastructure Registries

Domain Owner:
Citizen Identity

Primary Responsibility:

- Register citizens
- Issue Nexa Citizen IDs
- Verify citizen identity
- Manage citizen identity lifecycle

Authoritative Identifier:

- Nexa Citizen ID

---

## 4.2 Birth Registry

Registry Family:
Core Infrastructure Registries

Domain Owner:
Birth Records

Primary Responsibility:

- Register births
- Issue Birth Certificate Reference Numbers
- Verify birth records

Authoritative Identifier:

- Birth Certificate Reference Number

---

## 4.3 National Identity Registry

Registry Family:
Core Infrastructure Registries

Domain Owner:
National Identity Documents

Primary Responsibility:

- Manage simulated National Identity records
- Issue National Identity Numbers
- Verify National Identity information

Authoritative Identifier:

- National Identity Number

---

## 4.4 Revenue Registry

Registry Family:
Core Infrastructure Registries

Domain Owner:
Tax Administration

Primary Responsibility:

- Register taxpayers
- Issue NRA PINs
- Maintain taxpayer records

Authoritative Identifier:

- NRA PIN

---

## 4.5 Business Registry

Registry Family:
Core Infrastructure Registries

Domain Owner:
Businesses

Primary Responsibility:

- Register businesses
- Issue Business Registration Numbers
- Maintain business registration records

Authoritative Identifier:

- Business Registration Number

---

## 4.6 Telecom Registry

Registry Family:
Core Infrastructure Registries

Domain Owner:
Telecommunications

Primary Responsibility:

- Issue telephone numbers
- Manage number allocation
- Verify active numbers

Authoritative Identifier:

- NexaCom Phone Number

---

## 4.7 SIM Registry

Registry Family:
Core Infrastructure Registries

Domain Owner:
SIM Cards

Primary Responsibility:

- Register SIM cards
- Manage SIM ownership
- Link SIMs to phone numbers

Authoritative Identifier:

- SIM ID / ICCID

---

## 4.8 Banking Registry

Registry Family:
Core Infrastructure Registries

Domain Owner:
Bank Accounts

Primary Responsibility:

- Issue bank account numbers
- Register bank accounts
- Maintain account ownership

Authoritative Identifier:

- Bank Account Number

---

## 4.9 Bank Card Registry

Registry Family:
Core Infrastructure Registries

Domain Owner:
Bank Cards

Primary Responsibility:

- Issue payment card numbers
- Manage payment cards
- Link cards to bank accounts

Authoritative Identifier:

- Bank Card Number

---

## 4.10 Employer Registry

Registry Family:
Nexa Ecosystem Registries

Domain Owner:
Employers

Primary Responsibility:

- Register employers
- Issue Employer IDs
- Maintain employer identity records

Authoritative Identifier:

- Employer ID

---

## 4.11 Employee Registry

Registry Family:
Nexa Ecosystem Registries

Domain Owner:
Employees

Primary Responsibility:

- Register employees
- Issue Employee IDs
- Link employees to employers

Authoritative Identifier:

- Employee ID

---

## 4.12 Device Registry

Registry Family:
Nexa Ecosystem Registries

Domain Owner:
Physical Devices

Primary Responsibility:

- Register devices
- Issue Nexa Device IDs
- Maintain trusted device records

Examples include:

- NexaPOS terminals
- QR scanners
- Receipt printers
- Customer displays
- Weighing scales
- Future Nexa hardware

Authoritative Identifier:

- Nexa Device ID

---

## 4.13 NexaPesa Merchant Registry

Registry Family:
Nexa Ecosystem Registries

Domain Owner:
Digital Payment Merchants

Primary Responsibility:

- Register merchants
- Issue Merchant Numbers
- Issue Till Numbers

Authoritative Identifiers:

- Merchant Number
- Till Number

---

## 4.14 Identity Registry

Registry Family:
Nexa Ecosystem Registries

Domain Owner:
Nexa Ecosystem Identity

Primary Responsibility:

- Manage NexaID lifecycle
- Coordinate collaborative NexaID minting
- Verify ecosystem identity
- Activate NexaID
- Maintain NexaID trust status

Authoritative Identifier:

- NexaID

---

# 5. Registry Independence

Each registry shall operate independently.

Registries may reference one another through approved interfaces but shall not directly modify another registry's internal records.

---

# 6. Future Registry Expansion

The Master Registry Foundation is designed for expansion.

Future registry domains may be introduced without affecting existing registries, provided they:

- define a unique business domain;
- own a unique immutable identifier;
- belong to an approved registry family;
- conform to MR-001;
- are approved through the platform architecture governance process.

---

End of MR-002 (Version 1.0 Draft)