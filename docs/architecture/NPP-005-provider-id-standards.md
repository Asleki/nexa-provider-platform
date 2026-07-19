# NPP-005 — Provider ID Standards

**Document ID:** NPP-005  
**Title:** Provider ID Standards  
**Project:** Nexa Provider Platform (NPP)  
**Status:** Draft  
**Version:** 0.1.0  
**Author:** NexTech Kenya Limited  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines the permanent identifier standards used throughout the Nexa Provider Platform.

Every provider record shall have one immutable identifier assigned at creation.

Identifiers must never be reused.

Identifiers must never change during the lifetime of a record.

---

# 2. Design Principles

Provider identifiers shall be:

- Globally unique
- Immutable
- Human readable
- Machine sortable where practical
- Independent of storage technology
- Independent of runtime mode
- Safe for future synchronization
- Compatible with JSON, CSV, PostgreSQL and APIs

---

# 3. General Format

The standard identifier format is:

```text
<PREFIX>-<YEAR><MONTH><DAY>-<RANDOM>
```

Example:

```text
CIT-20260718-A7F29C4D
```

Where:

- Prefix identifies the record type.
- Date indicates creation date.
- Random component guarantees uniqueness.

---

# 4. Identity Domain IDs

## Citizen

```text
CIT-YYYYMMDD-XXXXXXXX
```

Example:

```text
CIT-20260718-A7F29C4D
```

---

## Identity Document

```text
IDN-YYYYMMDD-XXXXXXXX
```

---

## Birth Certificate

```text
BRC-YYYYMMDD-XXXXXXXX
```

---

# 5. Business Registry IDs

## Business

```text
BUS-YYYYMMDD-XXXXXXXX
```

---

## Business Owner

```text
OWN-YYYYMMDD-XXXXXXXX
```

---

## Director

```text
DIR-YYYYMMDD-XXXXXXXX
```

---

# 6. Banking IDs

## Bank

```text
BNK-YYYYMMDD-XXXXXXXX
```

---

## Branch

```text
BRH-YYYYMMDD-XXXXXXXX
```

---

## Bank Account

```text
ACC-YYYYMMDD-XXXXXXXX
```

---

## Transaction

```text
TXN-YYYYMMDD-XXXXXXXX
```

---

# 7. Mobile Money IDs

## Wallet

```text
WAL-YYYYMMDD-XXXXXXXX
```

---

## Merchant

```text
MER-YYYYMMDD-XXXXXXXX
```

---

## Agent

```text
AGT-YYYYMMDD-XXXXXXXX
```

---

# 8. Telecommunications IDs

## SIM

```text
SIM-YYYYMMDD-XXXXXXXX
```

---

## Mobile Number

```text
MSI-YYYYMMDD-XXXXXXXX
```

---

## Device

```text
DEV-YYYYMMDD-XXXXXXXX
```

---

# 9. Tax IDs

## Taxpayer

```text
TAX-YYYYMMDD-XXXXXXXX
```

---

## Tax Reference

```text
TRF-YYYYMMDD-XXXXXXXX
```

---

# 10. Insurance IDs

## Member

```text
MEM-YYYYMMDD-XXXXXXXX
```

---

## Policy

```text
POL-YYYYMMDD-XXXXXXXX
```

---

## Claim

```text
CLM-YYYYMMDD-XXXXXXXX
```

---

# 11. Platform IDs

## API Client

```text
CLI-YYYYMMDD-XXXXXXXX
```

---

## Webhook

```text
WHK-YYYYMMDD-XXXXXXXX
```

---

## Provider Event

```text
PEV-YYYYMMDD-XXXXXXXX
```

---

## Audit Record

```text
AUD-YYYYMMDD-XXXXXXXX
```

---

## Request

```text
REQ-YYYYMMDD-XXXXXXXX
```

---

## Correlation

```text
COR-YYYYMMDD-XXXXXXXX
```

---

# 12. Reserved Prefixes

The following prefixes are reserved:

| Prefix | Purpose |
|---------|---------|
| CIT | Citizen |
| IDN | Identity Document |
| BRC | Birth Certificate |
| BUS | Business |
| OWN | Business Owner |
| DIR | Director |
| BNK | Bank |
| BRH | Branch |
| ACC | Bank Account |
| TXN | Transaction |
| WAL | Wallet |
| MER | Merchant |
| AGT | Mobile Money Agent |
| SIM | SIM Registration |
| MSI | Mobile Number |
| DEV | Device |
| TAX | Taxpayer |
| TRF | Tax Reference |
| MEM | Insurance Member |
| POL | Insurance Policy |
| CLM | Insurance Claim |
| CLI | API Client |
| WHK | Webhook |
| PEV | Provider Event |
| AUD | Audit Record |
| REQ | Request |
| COR | Correlation |

---

# 13. Identifier Rules

Every identifier:

- is generated once;
- is immutable;
- must never be recycled;
- must never encode confidential information;
- remains valid regardless of storage technology;
- remains valid after synchronization.

---

# 14. Future Compatibility

The identifier standard must remain unchanged when migrating from:

- JSON
- CSV
- Supabase PostgreSQL
- FastAPI
- External provider integrations

No storage migration should require changing provider identifiers.

---

# 15. Guiding Principle

Identifiers represent the permanent identity of provider records.

Business attributes may change over time.

Identifiers must never change.