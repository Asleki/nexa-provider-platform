=========================================================
MR-011 — Nexa Citizen ID vs NexaID Specification
Master Registry Foundation
NPP-M006.1
Status: Draft
=========================================================

1. Purpose

This document defines the distinction between the Nexa Citizen ID and the
NexaID within the Nexa Provider Platform (NPP).

Although both identifiers relate to identity, they serve different purposes,
have different issuance authorities, and follow different lifecycle rules.

This specification ensures that every system across the Nexa ecosystem uses
both identifiers consistently and without ambiguity.

─────────────────────────────────────────────────────────

2. Guiding Principle

A person is identified once.

That identity may participate in many businesses, services, roles,
organizations, and transactions.

The permanent identity remains stable while operational relationships evolve.

─────────────────────────────────────────────────────────

3. Nexa Citizen ID

Definition

The Nexa Citizen ID is the permanent identity assigned to an individual
recognized by the Nexa ecosystem.

Purpose

• Establish a single lifelong identity.
• Prevent duplicate person records.
• Support identity verification.
• Enable trusted participation across services.
• Act as the root person identifier.

Characteristics

• Globally unique.
• Permanently assigned.
• Never reused.
• Never reassigned.
• Remains valid throughout the person's lifecycle.

─────────────────────────────────────────────────────────

4. NexaID

Definition

The NexaID is the operational identity used by applications, registries,
services, and business modules to reference an active participant.

Purpose

• Authenticate users.
• Link services.
• Reference operational records.
• Support permissions.
• Connect multiple registries.

Characteristics

• Globally unique.
• Derived after successful identity registration.
• May reference a person, organization, or system entity.
• Used daily by applications.
• May be suspended or retired without affecting the underlying Citizen ID.

─────────────────────────────────────────────────────────

5. Relationship

One Nexa Citizen ID

↓

One Person

↓

One Active NexaID

↓

Many Services

↓

Many Transactions

↓

Many Registry References

The Citizen ID identifies the individual.

The NexaID enables participation within the platform.

─────────────────────────────────────────────────────────

6. Comparison

Nexa Citizen ID

Purpose:
Permanent identity

Owner:
Individual

Lifetime:
Permanent

Changes:
Never reassigned

Primary Use:
Identity

Registry:
Citizen Registry

─────────────────────────────────────────────────────────

NexaID

Purpose:
Operational participation

Owner:
Citizen, organization or system entity

Lifetime:
Operational lifecycle

Changes:
Lifecycle controlled

Primary Use:
Platform operations

Registry:
Identity Registry

─────────────────────────────────────────────────────────

7. Issuance

Nexa Citizen ID

Issued once after successful identity verification.

NexaID

Issued after successful platform registration and activation.

─────────────────────────────────────────────────────────

8. Lifecycle

Citizen ID

Created

Verified

Active

Deceased (where applicable)

Archived

Citizen ID is never reused.

NexaID

Pending

Active

Suspended

Locked

Reactivated

Retired

Archived

─────────────────────────────────────────────────────────

9. Immutability

Citizen ID

The identifier itself is permanently immutable.

NexaID

The identifier value is immutable.

Operational status may change through controlled lifecycle events.

─────────────────────────────────────────────────────────

10. Cross-Registry Usage

Both identifiers may be referenced by:

Supplier Registry

Customer Registry

Employee Registry

Manufacturer Registry

Warehouse Registry

Asset Registry

Device Registry

Financial Registry

Provider Registry

Future registries

Cross-registry references shall never duplicate identity information.

─────────────────────────────────────────────────────────

11. Security

Neither identifier shall expose sensitive personal information.

Authentication shall never rely solely on either identifier.

Both identifiers must support audit logging and access control.

─────────────────────────────────────────────────────────

12. Future Compatibility

This specification applies to every future Nexa ecosystem application,
including future identity, finance, healthcare, education, government,
manufacturing, logistics, and partner platforms.

Future registries shall use these identifiers without changing their meaning.

=========================================================
End of MR-011
=========================================================