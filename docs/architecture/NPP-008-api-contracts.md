# NPP-008 — API Contracts

**Document ID:** NPP-008  
**Title:** API Contracts  
**Project:** Nexa Provider Platform (NPP)  
**Status:** Draft  
**Version:** 0.1.0  
**Author:** NexTech Kenya Limited  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines the communication contracts used by the Nexa Provider Platform.

Although the initial implementation is terminal-based, all provider services must be designed so they can later be exposed through APIs without changing business logic.

API contracts define how external systems communicate with NPP.

---

# 2. Design Principles

Every API contract shall be:

- Versioned
- Predictable
- Stateless
- Secure
- Technology independent
- Backward compatible where practical
- Validation driven
- Audit logged

Business services must remain independent from transport technologies.

---

# 3. Consumer Systems

The Nexa Provider Platform may be consumed by:

- NexaPOS Alpha
- Future Nexa applications
- Developer tools
- Testing utilities
- Approved external integrations

All consumers use the same provider services.

---

# 4. Communication Architecture

Current Phase

```text
CLI
      │
      ▼
Provider Services
```

Future Phase

```text
HTTP Request
        │
        ▼
FastAPI
        │
        ▼
Provider Services
        │
        ▼
Repository Layer
```

The API layer translates requests.

Business rules remain inside Provider Services.

---

# 5. API Versioning

Every public endpoint shall include a version.

Example:

```text
/api/v1/
```

Future versions may include:

```text
/api/v2/
/api/v3/
```

Older versions should remain supported according to platform compatibility policies.

---

# 6. Request Structure

Every request should include:

- Request ID
- Timestamp
- Runtime Mode
- Client ID
- Authentication Token
- Correlation ID
- Payload

Optional fields:

- Idempotency Key
- Device ID
- API Version

---

# 7. Response Structure

Every response should include:

- Success
- Status Code
- Request ID
- Correlation ID
- Timestamp
- Result
- Message

Optional fields:

- Provider Event ID
- Audit ID
- Validation Errors

---

# 8. Standard Status Codes

Typical responses include:

| Code | Meaning |
|------|---------|
| 200 | Success |
| 201 | Created |
| 400 | Validation Error |
| 401 | Authentication Required |
| 403 | Permission Denied |
| 404 | Record Not Found |
| 409 | Conflict |
| 422 | Business Rule Failed |
| 500 | Internal Error |

---

# 9. Authentication

Future API access shall require authentication.

Possible mechanisms include:

- API Keys
- OAuth
- JWT
- Service Accounts

The authentication mechanism may evolve without changing Provider Services.

---

# 10. Authorization

Authorization determines what operations a client may perform.

Examples:

- Read Citizens
- Register Businesses
- Verify Identity
- Create Wallet
- View Audit Records

Permissions must be validated before Provider Services execute.

---

# 11. Idempotency

Operations that create or modify provider records should support idempotency.

Repeated requests with the same Idempotency Key should produce the same result without creating duplicate records.

---

# 12. Validation

All requests must be validated before reaching Provider Services.

Validation includes:

- Required fields
- Data formats
- Business rules
- Authorization
- Runtime Mode

Invalid requests must not modify provider records.

---

# 13. Error Handling

Errors should be predictable.

Responses should provide:

- Error Code
- Human-readable Message
- Validation Details (where appropriate)
- Request ID
- Correlation ID

Internal implementation details should never be exposed.

---

# 14. Relationship to Events

Successful operations may generate:

- Provider Events
- Audit Records

API contracts define communication only.

They do not define provider business rules.

---

# 15. Future Integrations

Future API consumers may include:

- NexaPOS Alpha
- NexVox
- Mobile Applications
- Administrative Portals
- Developer Portal
- Approved Third-party Systems

All integrations should use the same standardized contracts.

---

# 16. Technology Independence

The API contract remains stable regardless of implementation.

Possible implementations include:

- FastAPI
- REST
- GraphQL
- Internal Service Calls
- Future Gateway Services

Business services must not depend on any specific API framework.

---

# 17. Security Principles

Every API interaction should support:

- Authentication
- Authorization
- Encryption in transit
- Audit Logging
- Request Validation
- Rate Limiting
- Idempotency
- Versioning

Security is enforced before Provider Services execute.

---

# 18. Guiding Principle

API contracts define how systems communicate with the Nexa Provider Platform.

Provider Services define what the platform does.

Keeping communication separate from business logic ensures the platform remains modular, maintainable and adaptable as new technologies are introduced.