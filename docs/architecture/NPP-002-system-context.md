# NPP-002 — System Context

**Document ID:** NPP-002  
**Title:** System Context  
**Project:** Nexa Provider Platform (NPP)  
**Status:** Draft  
**Version:** 0.1.0  
**Author:** NexTech Kenya Limited  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines how the Nexa Provider Platform (NPP) fits within the Nexa ecosystem and how it interacts with other systems.

It establishes clear ownership boundaries and communication paths to ensure each platform has a single, well-defined responsibility.

---

# 2. Position Within the Nexa Ecosystem

The Nexa Provider Platform is a shared provider service for the Nexa ecosystem.

It is not a business application.

It is not a point-of-sale system.

It is not an accounting system.

Its responsibility is to represent external institutions and provide trusted provider facts to authorized consumer systems.

---

# 3. High-Level Context

```text
                    External Institutions
                             │
                             ▼
                Nexa Provider Platform (NPP)
                             │
                Provider APIs / Contracts
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    NexaPOS Alpha      Future Systems      Developer Tools
```

---

# 4. Relationship with NexaPOS Alpha

NexaPOS Alpha is the primary consumer of provider information.

NPP provides provider-owned facts such as:

- Identity verification
- Business registration status
- Bank information
- Mobile wallet information
- SIM registration
- Tax status
- Insurance eligibility

NexaPOS Alpha consumes these facts but remains responsible for its own business decisions.

---

# 5. Ownership Boundary

NPP owns:

- Citizens
- Identity records
- Businesses
- Banks
- Bank branches
- Bank accounts
- Mobile wallets
- SIM registrations
- Taxpayer records
- Insurance records
- Provider events
- Provider audit logs
- API clients
- Webhook registrations

NexaPOS Alpha owns:

- Customers
- Suppliers
- Employees
- Sales
- Purchases
- Inventory
- Finance ledgers
- Payroll
- Operational workflows
- Internal dashboards
- Estate operations

The two systems must not directly modify each other's records.

---

# 6. Communication Model

Communication between systems must occur through approved interfaces.

Current phase:

```text
NexaPOS Alpha
      │
Export / Import
      │
NPP
```

Future phase:

```text
NexaPOS Alpha
      │
Provider Gateway
      │
HTTPS
      │
FastAPI
      │
Nexa Provider Platform
```

No system may access another system's storage directly.

---

# 7. Offline Relationship

Both systems are designed to operate offline.

When offline:

- NPP continues using local provider storage.
- NexaPOS Alpha continues using its local provider cache.
- Synchronization occurs when connectivity returns.

---

# 8. Future External Providers

The current platform simulates providers.

Future provider adapters may connect to:

- Government identity services
- Banking institutions
- Mobile money operators
- Telecom providers
- Tax authorities
- Insurance providers

Consumer systems should not need to distinguish between simulated and real providers.

---

# 9. Relationship with NexVox

NPP provides approved simulation data for future NexVox analysis.

Possible future integrations include:

- Provider-health analytics
- Synthetic training datasets
- Simulation reports

NexVox does not directly modify provider records.

---

# 10. Security Boundary

Every request between NPP and consumer systems must eventually support:

- Authentication
- Authorization
- Request validation
- Audit logging
- Idempotency
- Versioned contracts

Direct database access between systems is prohibited.

---

# 11. Guiding Principle

The Nexa Provider Platform is the trusted provider-information layer of the Nexa ecosystem.

It owns provider facts.

Consumer systems own business decisions.

Maintaining this separation ensures that each platform remains modular, secure, independently deployable, and easier to evolve over time.