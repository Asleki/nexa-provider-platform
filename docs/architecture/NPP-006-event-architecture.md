# NPP-006 — Event Architecture

**Document ID:** NPP-006  
**Title:** Event Architecture  
**Project:** Nexa Provider Platform (NPP)  
**Status:** Draft  
**Version:** 0.1.0  
**Author:** NexTech Kenya Limited  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines the event architecture used by the Nexa Provider Platform.

Provider events represent immutable records describing actions that have occurred within the platform.

Events provide a complete historical record of provider activity and support auditing, synchronization, replay, troubleshooting and future integrations.

---

# 2. Event Principles

Every provider event shall be:

- Immutable
- Append-only
- Versioned
- Timestamped
- Independently identifiable
- Storage independent
- Replayable
- Synchronization ready

Events must never be edited after creation.

---

# 3. Event Lifecycle

Provider Action

↓

Validation

↓

Business Service

↓

Provider Event Created

↓

Event Stored

↓

Audit Record Created

↓

Provider State Updated

Events describe what happened.

Provider records describe the current state.

---

# 4. Event Categories

The platform supports several event categories.

## Identity Events

Examples:

- PROVIDER.CITIZEN_REGISTERED
- PROVIDER.IDENTITY_VERIFIED
- PROVIDER.IDENTITY_UPDATED
- PROVIDER.IDENTITY_SUSPENDED
- PROVIDER.IDENTITY_REACTIVATED

---

## Business Registry Events

Examples:

- PROVIDER.BUSINESS_REGISTERED
- PROVIDER.BUSINESS_UPDATED
- PROVIDER.BUSINESS_VERIFIED
- PROVIDER.BUSINESS_SUSPENDED

---

## Banking Events

Examples:

- PROVIDER.BANK_CREATED
- PROVIDER.BRANCH_CREATED
- PROVIDER.ACCOUNT_CREATED
- PROVIDER.ACCOUNT_CLOSED
- PROVIDER.DEPOSIT_COMPLETED
- PROVIDER.WITHDRAWAL_COMPLETED
- PROVIDER.TRANSFER_COMPLETED
- PROVIDER.TRANSACTION_REVERSED

---

## Mobile Money Events

Examples:

- PROVIDER.WALLET_CREATED
- PROVIDER.WALLET_VERIFIED
- PROVIDER.MOBILE_PAYMENT_COMPLETED
- PROVIDER.MOBILE_TRANSFER_COMPLETED

---

## Telecommunications Events

Examples:

- PROVIDER.SIM_REGISTERED
- PROVIDER.SIM_REPLACED
- PROVIDER.SIM_SUSPENDED
- PROVIDER.PHONE_NUMBER_ASSIGNED

---

## Tax Events

Examples:

- PROVIDER.TAXPAYER_REGISTERED
- PROVIDER.TAX_STATUS_UPDATED
- PROVIDER.TAX_PAYMENT_RECORDED

---

## Insurance Events

Examples:

- PROVIDER.INSURANCE_MEMBER_REGISTERED
- PROVIDER.POLICY_CREATED
- PROVIDER.CLAIM_SUBMITTED
- PROVIDER.CLAIM_APPROVED

---

## Platform Events

Examples:

- PROVIDER.API_CLIENT_REGISTERED
- PROVIDER.WEBHOOK_REGISTERED
- PROVIDER.SYNC_COMPLETED
- PROVIDER.EXPORT_COMPLETED

---

# 5. Event Structure

Every event should contain:

- Event ID
- Event Type
- Aggregate Type
- Aggregate ID
- Event Version
- Timestamp
- Runtime Mode
- Correlation ID
- Request ID
- Actor
- Source
- Payload

---

# 6. Event Storage

During Phase 1 all events are stored locally.

Example:

```text
storage/events/provider-events.jsonl
```

Each line contains one complete event.

Events are appended.

Existing events are never modified.

---

# 7. Event Naming Standard

Event names follow:

```text
PROVIDER.<ENTITY>_<ACTION>
```

Examples:

```text
PROVIDER.CITIZEN_REGISTERED

PROVIDER.BUSINESS_REGISTERED

PROVIDER.SIM_REGISTERED

PROVIDER.ACCOUNT_CREATED

PROVIDER.TRANSACTION_REVERSED
```

Names should be:

- Past tense
- Explicit
- Human readable
- Stable

---

# 8. Event Versioning

Each event contains:

- Event Version
- Schema Version

New schema versions must remain backward compatible whenever practical.

---

# 9. Event Replay

Because events are immutable they may later support:

- rebuilding read models;
- synchronization recovery;
- debugging;
- replay testing;
- analytics.

Replay capability is a future feature.

---

# 10. Relationship to Provider Records

Provider records contain the latest known state.

Events describe how that state changed.

Example:

Citizen Record

```text
Status = VERIFIED
```

Historical Events

```text
PROVIDER.CITIZEN_REGISTERED

PROVIDER.IDENTITY_VERIFIED
```

Both are required.

---

# 11. Relationship to Audit

Events describe business activity.

Audit records describe system activity.

Example:

Business Event

```text
PROVIDER.SIM_REGISTERED
```

Audit Record

```text
CLI user registered SIM using Identity Service.
```

Events and audit records complement one another.

---

# 12. Future Integration

Future integrations may consume provider events through:

- FastAPI
- Webhooks
- Event streaming
- Synchronization services
- Analytics pipelines

The event format should remain stable regardless of transport mechanism.

---

# 13. Guiding Principle

Provider events form the permanent historical record of the Nexa Provider Platform.

Current provider records may change over time.

Provider events must never change.