# =========================================================
# MR-005 — Identifier Lifecycle Rules
# =========================================================

Version: 1.0 (Draft)

Status: Draft

Architecture Family:
Master Registry Foundation

Milestone:
NPP-M006.1 — Master Registry Architecture & Identifier Catalogue

---

# 1. Purpose

The Identifier Lifecycle Rules define the complete lifecycle of every immutable identifier governed by the Master Registry Foundation.

This document establishes how identifiers are requested, issued, activated, verified, referenced, suspended, retired and audited while ensuring they remain unique, immutable and traceable throughout their lifetime.

---

# 2. Scope

This document defines:

- Identifier lifecycle stages
- State transitions
- Lifecycle ownership
- Activation rules
- Suspension rules
- Retirement rules
- Audit requirements

---

# 3. Lifecycle Principles

Every identifier shall:

- have one identifiable lifecycle;
- be created only once;
- never be reused;
- remain permanently traceable;
- retain complete historical records;
- support authorised verification throughout its lifetime.

---

# 4. Standard Lifecycle

Every identifier progresses through the following lifecycle.

```
Request
    │
    ▼
Validation
    │
    ▼
Issuance
    │
    ▼
Activation
    │
    ▼
Operational Use
    │
    ▼
Verification
    │
    ▼
Suspension (Optional)
    │
    ▼
Reactivation (Optional)
    │
    ▼
Retirement
    │
    ▼
Permanent Audit Archive
```

---

# 5. Lifecycle Stages

## 5.1 Request

An authorised system requests creation of a new identifier.

No identifier exists at this stage.

---

## 5.2 Validation

The issuing registry validates all required information before issuing an identifier.

Validation may include:

- uniqueness checks;
- ownership verification;
- prerequisite verification;
- policy validation.

---

## 5.3 Issuance

The registry permanently allocates the identifier.

Once issued:

- the identifier becomes immutable;
- duplicate issuance is prohibited;
- reuse is prohibited.

---

## 5.4 Activation

The identifier becomes available for operational use.

Activation requirements depend on the issuing registry.

---

## 5.5 Operational Use

The identifier may now be:

- referenced;
- validated;
- linked;
- audited.

Ownership remains unchanged.

---

## 5.6 Verification

Authorised systems may verify the identifier without modifying it.

Verification never changes ownership or lifecycle state.

---

## 5.7 Suspension

Where permitted by policy, identifiers may be suspended.

Suspension temporarily restricts operational use while preserving ownership and historical integrity.

---

## 5.8 Reactivation

Suspended identifiers may be restored following successful verification and authorisation.

The original identifier remains unchanged.

---

## 5.9 Retirement

An identifier may be retired when it permanently reaches the end of its operational lifecycle.

Retirement does not delete the identifier.

---

## 5.10 Permanent Audit Archive

Every retired identifier remains permanently available for authorised auditing.

Historical records shall never be destroyed.

---

# 6. Lifecycle Ownership

Only the issuing registry may change an identifier's lifecycle state.

Business applications may request lifecycle actions but shall not perform lifecycle transitions directly.

---

# 7. Lifecycle Restrictions

Identifiers shall never:

- be reassigned;
- be renumbered;
- be duplicated;
- be recycled;
- be permanently deleted.

---

# 8. Future Lifecycle Extensions

Individual registries may introduce additional lifecycle states provided they:

- remain compatible with this document;
- preserve identifier immutability;
- maintain complete auditability;
- receive architectural approval.

---

End of MR-005 (Version 1.0 Draft)