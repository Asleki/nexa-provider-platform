# NPP-012 — Runtime Modes

**Document ID:** NPP-012  
**Title:** Runtime Modes  
**Project:** Nexa Provider Platform (NPP)  
**Status:** Draft  
**Version:** 0.1.0  
**Author:** NexTech Kenya Limited  
**Last Updated:** 2026-07-18

---

# 1. Purpose

This document defines the runtime modes supported by the Nexa Provider Platform (NPP).

Runtime modes determine how the platform behaves in different environments without requiring changes to the underlying business logic.

By separating runtime behavior from business services, the platform remains predictable, testable and maintainable throughout its lifecycle.

---

# 2. Design Principles

Runtime modes shall be:

- Explicitly configured
- Mutually exclusive
- Predictable
- Auditable
- Environment independent
- Secure by default

Provider Services must never infer the runtime mode.

The active runtime mode shall be supplied through the platform configuration.

---

# 3. Supported Runtime Modes

The platform supports the following runtime modes:

| Mode | Purpose |
|------|---------|
| Development | Local software development |
| Testing | Automated and manual testing |
| Simulation | Simulated provider operations |
| Staging | Pre-production validation |
| Production | Live operational environment |

Only one runtime mode may be active at a time.

---

# 4. Development Mode

Development mode is intended for local engineering work.

Characteristics include:

- Local JSON storage
- Verbose logging
- Mock provider data
- Debug utilities
- Developer tooling
- Local CLI execution

Development mode prioritizes rapid iteration over operational performance.

---

# 5. Testing Mode

Testing mode supports automated verification of platform functionality.

Characteristics include:

- Isolated test data
- Repeatable execution
- Temporary repositories
- Automated cleanup
- Mock integrations
- Deterministic outputs

Testing mode should never modify production data.

---

# 6. Simulation Mode

Simulation mode allows provider workflows to be exercised without interacting with live external systems.

Characteristics include:

- Simulated provider responses
- Generated test records
- Mock transactions
- Event generation
- Audit generation

Simulation mode enables realistic operational testing while ensuring that no live provider records are affected.

---

# 7. Staging Mode

Staging mode mirrors the production environment as closely as practical.

Characteristics include:

- Production-like configuration
- Real infrastructure where appropriate
- Controlled datasets
- Integration validation
- Deployment verification

Staging exists to validate releases before production deployment.

---

# 8. Production Mode

Production mode is the live operational environment.

Characteristics include:

- Live provider records
- Live integrations
- Secure authentication
- Operational monitoring
- Full auditing
- Controlled configuration

Production mode prioritizes stability, security and reliability.

---

# 9. Runtime Configuration

The runtime mode shall be defined through platform configuration.

Example values include:

```text
development
testing
simulation
staging
production
```

Runtime configuration should be loaded during platform startup.

---

# 10. Runtime Behaviour

Runtime mode may influence:

- Logging verbosity
- Repository implementation
- External integrations
- Error reporting
- Synchronization
- Debug utilities
- Test data availability

Business rules must remain consistent across all runtime modes unless explicitly documented.

---

# 11. Relationship to Events

Every provider event should include the active runtime mode.

Example:

```text
runtime_mode = production
```

This allows historical events to be interpreted correctly.

---

# 12. Relationship to Audit

Every audit record should include the active runtime mode.

Example:

```text
runtime_mode = testing
```

This enables separation of operational and non-operational activity.

---

# 13. Security Considerations

Development and testing utilities must never be available in production mode.

Simulation data must never be transmitted to live provider systems.

Production secrets must never be stored in development configuration.

---

# 14. Future Expansion

Additional runtime modes may be introduced as the platform evolves.

Examples include:

- Disaster Recovery
- Performance Benchmarking
- Training Environment
- Demonstration Environment

Future runtime modes should remain compatible with the existing runtime architecture.

---

# 15. Guiding Principle

Runtime modes define *where* the platform is operating.

Provider Services define *what* the platform does.

Separating runtime behavior from business logic ensures consistent functionality across development, testing and production environments while supporting future expansion.