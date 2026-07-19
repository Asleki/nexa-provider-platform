# NPP-013 — Data Ownership

**Document ID:** NPP-013  
**Title:** Data Ownership  
**Project:** Nexa Provider Platform (NPP)  
**Status:** Draft  
**Version:** 0.1.0  
**Author:** NexTech Kenya Limited  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines ownership responsibilities for all data managed by the Nexa Provider Platform (NPP).

Data ownership ensures every provider record has a single authoritative source responsible for its lifecycle, integrity and governance.

This prevents duplication, conflicting updates and inconsistent information across the wider Nexa ecosystem.

---

# 2. Design Principles

Data ownership shall follow these principles:

- Single source of truth
- Clear ownership
- Controlled synchronization
- Explicit authority
- Auditability
- Traceability
- Security by design

Every record must have one authoritative owner.

---

# 3. Single Source of Truth

Each provider record shall be owned by exactly one provider domain.

Examples include:

| Provider Domain | Owns |
|----------------|------|
| Identity | Citizens, identity documents |
| Business Registry | Businesses, directors, owners |
| Banking | Banks, branches, accounts |
| Mobile Money | Wallets, agents, merchants |
| Telecommunications | SIM registrations, mobile numbers |
| Tax | Taxpayer records |
| Insurance | Members, policies, claims |

Only the owning domain may modify its records.

---

# 4. Consumer Systems

Other systems may consume provider information.

Examples include:

- NexaPOS Alpha
- Future Nexa applications
- Reporting systems
- Analytics platforms
- Administrative portals

Consumers must treat provider information as read-only unless explicitly authorized.

---

# 5. Ownership Responsibilities

The owning provider domain is responsible for:

- Record creation
- Record validation
- Record updates
- Record suspension
- Record reactivation
- Event generation
- Audit generation
- Data quality

Ownership includes responsibility for maintaining the integrity of provider records throughout their lifecycle.

---

# 6. Shared Data

Some information may be shared across domains.

Examples include:

- Citizen identifiers
- Business identifiers
- Provider status
- Verification status

Shared data remains owned by its originating provider.

Receiving systems must not assume ownership.

---

# 7. Synchronization

Synchronization distributes provider data.

Synchronization does not transfer ownership.

Receiving systems maintain local copies for operational purposes while recognizing the originating provider as the authoritative source.

---

# 8. Updates

Updates to provider records must originate from the owning provider.

Consumers requesting changes should submit requests through approved provider services.

Direct modification of synchronized copies is not permitted.

---

# 9. Data Integrity

Ownership ensures:

- No duplicate authority
- Predictable updates
- Consistent validation
- Reliable synchronization
- Accurate audit history

Competing ownership is prohibited.

---

# 10. Relationship to Events

Provider events originate from the owning provider.

Examples include:

```text
PROVIDER.CITIZEN_REGISTERED

PROVIDER.BUSINESS_REGISTERED

PROVIDER.WALLET_CREATED
```

Consumer systems should not generate provider events that alter another provider's authoritative records.

---

# 11. Relationship to Audit

Audit records document interactions with provider data.

Examples include:

- Provider record viewed
- Synchronization requested
- Validation failed
- Provider update completed

Audit records improve accountability without changing ownership.

---

# 12. Access Levels

Provider data access may be classified as:

| Access Level | Description |
|-------------|-------------|
| Read | View provider information |
| Create | Register new provider records |
| Update | Modify owned records |
| Suspend | Temporarily disable records |
| Reactivate | Restore suspended records |
| Administrative | Manage provider configuration |

Permissions must align with ownership responsibilities.

---

# 13. Future Integrations

Future integrations may request provider information through approved APIs.

Examples include:

- Banking integrations
- Government registries
- Insurance systems
- Mobile money providers
- Nexa ecosystem applications

External integrations must respect provider ownership boundaries.

---

# 14. Governance

Provider ownership policies should be reviewed whenever:

- A new provider domain is introduced.
- A provider domain is retired.
- Cross-domain workflows are expanded.
- Synchronization architecture changes.

Governance ensures ownership remains clear as the platform evolves.

---

# 15. Guiding Principle

Every provider record has one authoritative owner.

Many systems may consume provider information.

Only the owning provider is responsible for creating, validating, updating and maintaining the official record.

Maintaining clear ownership boundaries preserves consistency, trust and long-term maintainability across the Nexa Provider Platform.