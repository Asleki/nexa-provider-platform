# NPP-003 — Provider Domains

**Document ID:** NPP-003  
**Title:** Provider Domains  
**Project:** Nexa Provider Platform (NPP)  
**Status:** Draft  
**Version:** 0.1.0  
**Author:** NexTech Kenya Limited  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines the provider domains managed by the Nexa Provider Platform.

Each domain represents a logical external institution or service provider.

Domains are designed to be modular, independently maintainable and reusable across multiple Nexa applications.

---

# 2. Domain Principles

Every provider domain shall:

- own its provider records;
- validate its own business rules;
- expose standardized provider services;
- generate provider events;
- generate audit records;
- support offline operation;
- support future synchronization;
- remain independent from other domains where practical.

---

# 3. Identity Domain

## Purpose

Represents national identity and citizen information.

### Responsibilities

- Citizen registration
- Identity verification
- Identity lookup
- Identity status
- Birth registration
- Identity suspension
- Identity reactivation
- Duplicate detection

### Primary Records

- Citizens
- Identity documents
- Birth certificates
- Verification history
- Identity status

---

# 4. Business Registry Domain

## Purpose

Represents registered businesses.

### Responsibilities

- Business registration
- Business verification
- Business ownership
- Directors
- Registration status
- Business classification
- Operating status

### Primary Records

- Businesses
- Owners
- Directors
- Registration certificates
- Business categories

---

# 5. Banking Domain

## Purpose

Represents banking institutions.

### Responsibilities

- Bank registration
- Branch registration
- Account creation
- Account verification
- Deposits
- Withdrawals
- Transfers
- Reversals
- Statements
- Beneficiaries

### Primary Records

- Banks
- Branches
- Accounts
- Transactions
- Statements

---

# 6. Mobile Money Domain

## Purpose

Represents mobile-money providers.

### Responsibilities

- Wallet creation
- Merchant accounts
- Deposits
- Withdrawals
- Transfers
- Reversals
- Wallet verification
- Wallet status

### Primary Records

- Wallets
- Transactions
- Merchants
- Agents

---

# 7. Telecommunications Domain

## Purpose

Represents telecommunications providers.

### Responsibilities

- SIM registration
- SIM ownership
- SIM replacement
- SIM suspension
- SIM activation
- Device association
- Mobile number verification

### Primary Records

- SIM cards
- Mobile numbers
- Devices
- Subscribers

---

# 8. Tax Domain

## Purpose

Represents taxation authorities.

### Responsibilities

- Taxpayer registration
- Tax identification
- Compliance status
- VAT status
- Tax clearance
- Tax payment references

### Primary Records

- Taxpayers
- Tax references
- Compliance history

---

# 9. Insurance Domain

## Purpose

Represents insurance providers.

### Responsibilities

- Member registration
- Coverage verification
- Eligibility
- Contribution history
- Policy status
- Claims simulation

### Primary Records

- Members
- Policies
- Contributions
- Claims

---

# 10. API Client Domain

## Purpose

Represents systems authorized to consume provider services.

### Responsibilities

- Client registration
- API key management
- Scope assignment
- Authentication
- Authorization
- Request logging

### Primary Records

- Clients
- API keys
- Permissions
- Scopes

---

# 11. Webhook Domain

## Purpose

Represents outbound event subscriptions.

### Responsibilities

- Webhook registration
- Endpoint validation
- Event subscriptions
- Retry policies
- Delivery history
- Signature verification

### Primary Records

- Webhooks
- Deliveries
- Retry queues

---

# 12. Shared Domain Services

The following services are shared across all domains:

- ID generation
- Validation
- Event generation
- Audit logging
- Runtime mode
- Synchronization
- Configuration
- Security
- Time services

These shared services must not contain domain-specific business rules.

---

# 13. Domain Independence

Each provider domain should evolve independently.

Adding a new provider domain should not require changes to existing domains unless shared contracts are intentionally updated.

---

# 14. Future Domains

Future provider domains may include:

- Land Registry
- Education Registry
- Healthcare Registry
- Vehicle Registry
- Passport Services
- Border Control
- Utility Providers
- Credit Reference Bureaus
- Payment Networks
- International Identity Providers

The platform architecture must support adding new domains without redesigning the existing system.

---

# 15. Guiding Principle

Each provider domain represents an external institution.

The Nexa Provider Platform provides a consistent architectural model for all domains while allowing each provider to implement its own business rules, validation logic and operational workflows.