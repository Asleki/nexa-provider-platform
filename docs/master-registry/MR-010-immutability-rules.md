=========================================================
MR-010 — Immutability Rules
Master Registry Foundation
NPP-M006.1
Status: Draft
=========================================================

1. Purpose

The Immutability Rules define which registry records and identifier attributes
are permanent, which may be updated under controlled conditions, and how all
changes are recorded.

The objective is to preserve trust, traceability, auditability, and long-term
data integrity throughout the Nexa Provider Platform.

Immutability does not mean nothing can ever change.

It means that historical truth is never destroyed.

Every correction must preserve the complete history of the record.

─────────────────────────────────────────────────────────

2. Core Principles

The Registry Foundation follows these principles:

• Every identifier has a single immutable identity.
• Historical records must never be overwritten.
• Corrections create new audit records.
• Ownership changes never create a new identifier.
• Status changes never replace historical values.
• Deleted records remain recoverable through audit history.
• Every mutation must identify:
  - who performed it;
  - when it occurred;
  - why it occurred;
  - what changed;
  - who approved it.

─────────────────────────────────────────────────────────

3. Levels of Immutability

Level 1 — Permanently Immutable

Cannot ever be changed after issuance.

Examples:

• Registry ID
• Identifier ID
• Internal UUID
• Creation Timestamp
• Issuing Authority
• Initial Issuance Event
• Original Number Sequence
• Cryptographic Hash
• Parent Event Reference

Level 2 — Conditionally Mutable

May change only through an authorized workflow.

Examples:

• Display Name
• Contact Information
• Physical Address
• Email Address
• Phone Number
• Business Location
• Assigned Manager
• Notes

Every change requires:

• authorization;
• audit event;
• timestamp;
• actor;
• reason.

Level 3 — Lifecycle Controlled

These values represent the current operational state.

Examples:

ACTIVE

SUSPENDED

LOCKED

REVOKED

RETIRED

ARCHIVED

Each transition is recorded as a lifecycle event.

─────────────────────────────────────────────────────────

4. Immutable Registry Attributes

The following fields shall never change after creation.

Registry Identifier

Registry Namespace

Registry Type

Creation Event

Creation Timestamp

Issuing Authority

Original Sequence Number

Global UUID

Original Parent Registry Reference

Original Registry Family

Original Numbering Strategy

─────────────────────────────────────────────────────────

5. Immutable Identifier Attributes

Every identifier permanently retains:

Identifier Value

Internal UUID

Registry

Issuing Authority

Issue Timestamp

Original Owner

Issuance Event

Original Sequence Position

Check Digit (if used)

Hash Signature

Digital Verification Metadata

─────────────────────────────────────────────────────────

6. Mutable Attributes

The following information may be updated.

Legal Name

Trading Name

Telephone Number

Email

Postal Address

Physical Address

Preferred Language

Notification Preferences

Emergency Contact

Business Operating Hours

Additional Metadata

Every update creates:

Update Event

Audit Record

Version Number

Approval Record

─────────────────────────────────────────────────────────

7. Identifier Ownership

Ownership may change.

The identifier itself does not.

Example

Manufacturer changes company director.

Manufacturer ID remains identical.

Only ownership history changes.

Ownership history must include:

Previous Owner

New Owner

Effective Date

Authorizing Officer

Approval Reference

Reason

─────────────────────────────────────────────────────────

8. Lifecycle Events

Every registry record progresses through controlled lifecycle states.

Example

CREATED

VERIFIED

ACTIVE

SUSPENDED

REACTIVATED

REVOKED

RETIRED

ARCHIVED

Each transition creates an immutable lifecycle event.

─────────────────────────────────────────────────────────

9. Corrections

Incorrect information is never overwritten.

Instead:

Correction Event

↓

New Version

↓

Previous Version Preserved

This guarantees complete historical reconstruction.

─────────────────────────────────────────────────────────

10. Soft Deletion

Registry records are never permanently deleted through normal operation.

Instead they become:

Archived

Inactive

Retired

Revoked

Historical records remain searchable according to access permissions.

─────────────────────────────────────────────────────────

11. Audit Requirements

Every modification records:

Event ID

Registry

Identifier

Actor

Role

Device

Location

Timestamp

Reason

Approval Reference

Previous Value

New Value

Digital Signature

─────────────────────────────────────────────────────────

12. Cross-Registry Integrity

Changing one registry record shall never invalidate references from another registry.

If a supplier changes address:

Supplier ID remains unchanged.

Purchase Orders remain valid.

Warehouse Records remain valid.

Inventory History remains valid.

Audit references remain valid.

─────────────────────────────────────────────────────────

13. Event-Sourcing Compliance

The Registry Foundation follows the platform's event-sourcing principles.

No update destroys history.

Every change generates:

Create Event

Update Event

Ownership Event

Status Event

Correction Event

Retirement Event

Archive Event

The latest state is derived from immutable events.

─────────────────────────────────────────────────────────

14. Security Rules

Immutable fields cannot be edited through:

User Interface

API

Import Process

Synchronization

Administrative Console

Database Scripts

Only lifecycle events may alter operational status.

─────────────────────────────────────────────────────────

15. Future Compatibility

These immutability rules apply equally to future registries, including but not limited to:

Citizen Registry

Provider Registry

Manufacturer Registry

Warehouse Registry

Asset Registry

Device Registry

Vehicle Registry

Financial Registry

Healthcare Registry

Education Registry

Government Registry

Identity Registry

No future registry may weaken these guarantees without an approved platform architecture revision.

=========================================================
End of MR-010
=========================================================