# NPP-007 — Audit Architecture

**Document ID:** NPP-007  
**Title:** Audit Architecture  
**Project:** Nexa Provider Platform (NPP)  
**Status:** Draft  
**Version:** 0.1.0  
**Author:** NexTech Kenya Limited  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines the audit architecture used throughout the Nexa Provider Platform.

The audit system provides a permanent, chronological record of actions performed within the platform.

Unlike provider events, which describe business activity, audit records describe system activity.

Audit records support:

- accountability;
- troubleshooting;
- compliance;
- security investigations;
- synchronization diagnostics;
- operational monitoring.

---

# 2. Audit Principles

Every audit record shall be:

- Immutable
- Append-only
- Timestamped
- Versioned
- Independently identifiable
- Technology independent
- Synchronization ready
- Tamper evident

Audit records must never be modified after creation.

---

# 3. Audit Lifecycle

```text
User Request
      │
      ▼
Authentication
      │
      ▼
Validation
      │
      ▼
Business Service
      │
      ▼
Provider Event
      │
      ▼
Audit Record
      │
      ▼
Storage
```

Audit records are generated regardless of whether the operation succeeds or fails.

---

# 4. Audit Categories

The platform records several categories of audit activity.

## User Activity

Examples:

- Login
- Logout
- Command execution
- Provider lookup
- Record creation
- Record update
- Record suspension

---

## Security Activity

Examples:

- Authentication
- Authorization
- Invalid credentials
- Permission denial
- Security warnings

---

## Storage Activity

Examples:

- JSON write
- JSON read
- CSV export
- Backup creation
- Synchronization

---

## Integration Activity

Examples:

- API request
- API response
- Webhook delivery
- Webhook failure
- Synchronization completed

---

## System Activity

Examples:

- Startup
- Shutdown
- Configuration loaded
- Runtime mode changed
- Exception handled

---

# 5. Audit Record Structure

Every audit record should contain:

- Audit ID
- Timestamp
- Runtime Mode
- Request ID
- Correlation ID
- Actor
- Source
- Action
- Target
- Result
- Severity
- Message

Optional fields may include:

- Exception
- Stack Trace Reference
- Storage Adapter
- Client ID
- Device ID

---

# 6. Audit Storage

During Phase 1 all audit records are stored locally.

Example:

```text
storage/audit/provider-audit.jsonl
```

Each line contains one audit record.

Audit records are appended only.

Existing audit records must never be modified.

---

# 7. Audit Severity Levels

The following severity levels are supported.

## INFORMATION

Normal operational activity.

Examples:

- Citizen registered
- SIM assigned
- CSV exported

---

## WARNING

Unexpected but recoverable situations.

Examples:

- Duplicate registration attempt
- Invalid lookup
- Empty phone pool warning

---

## ERROR

Operations that failed.

Examples:

- Validation failure
- Storage failure
- Synchronization failure

---

## CRITICAL

Serious failures requiring investigation.

Examples:

- Audit storage unavailable
- Repository corruption
- Unauthorized access attempt
- Security integrity failure

---

# 8. Relationship to Provider Events

Provider Events describe business history.

Example:

```text
PROVIDER.CITIZEN_REGISTERED
```

Audit Records describe system history.

Example:

```text
Citizen registration executed through CLI by operator.
```

Both records should exist for significant operations.

---

# 9. Future Audit Integrations

Future audit records may be consumed by:

- FastAPI
- Monitoring services
- Analytics
- Reporting
- Security dashboards
- NexVox observational analysis

Audit records remain independent of the transport mechanism.

---

# 10. Audit Retention

Audit records are historical records.

They should not be deleted during normal operation.

Archiving strategies may be introduced in future platform versions.

---

# 11. Privacy

Audit records should not expose confidential information unnecessarily.

Sensitive values such as:

- passwords;
- authentication secrets;
- API keys;
- access tokens;
- encryption keys;

must never be stored in plain text within audit records.

---

# 12. Guiding Principle

Audit records provide the permanent operational history of the Nexa Provider Platform.

Provider records represent the current state.

Provider events represent business history.

Audit records represent system history.

Together they provide complete traceability across the platform.