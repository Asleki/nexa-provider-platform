"""
Nexa Provider Platform (NPP)
File: roadmap_data.py

Authoritative structured roadmap data for the NPP engineering roadmap.
Visible milestone numbers are positional and may be renumbered after insertion.
Internal record IDs are derived from semantic title paths so ordinary number
changes do not break identity. Completed milestone rows are preserved; new scope
is appended only to planned milestones and new planned root milestones.
"""
from __future__ import annotations
from hashlib import sha256
from types import MappingProxyType
from typing import Final, Iterable, Mapping

STATUS_COMPLETED: Final[str] = "COMPLETED"
STATUS_PLANNED: Final[str] = "PLANNED"
ALLOWED_STATUSES: Final[frozenset[str]] = frozenset({STATUS_COMPLETED, STATUS_PLANNED})
ROADMAP_VERSION: Final[str] = "1.1.0"
ROADMAP_TITLE: Final[str] = "Nexa Provider Platform — Final Scope Engineering Roadmap"
ROADMAP_START: Final[str] = "M001"
ROADMAP_END: Final[str] = "M030.12"

_ROADMAP_OUTLINE: Final[str] = r"""
C|M001|Project Foundation
C|M001.1|Repository Initialization
C|M001.2|Base Directory Structure
C|M001.3|Python Package Foundation
C|M001.4|Project Configuration
C|M001.5|Documentation Foundation
C|M001.6|Testing Foundation
C|M001.7|Git and Version-Control Foundation
C|M002|Core Contracts Foundation
C|M002.1|Base Contract Definitions
C|M002.2|Identifier Contracts
C|M002.3|Entity Contracts
C|M002.4|Repository Contracts
C|M002.5|Service Contracts
C|M002.6|Validation Contracts
C|M002.7|Serialization Contracts
C|M002.8|Contract Verification
C|M003|Shared Kernel Foundation
C|M003.1|Shared Types
C|M003.2|Shared Exceptions
C|M003.3|Shared Validation
C|M003.4|Shared Serialization
C|M003.5|Shared Metadata
C|M003.6|Shared Utilities
C|M003.7|Package Exports
C|M003.8|Shared Kernel Tests
C|M004|Storage Foundation
C|M004.1|Storage Contracts
C|M004.2|JSON Storage Foundation
C|M004.3|File Storage Utilities
C|M004.4|Serialization Support
C|M004.5|Storage Validation
C|M004.6|Storage Error Handling
C|M004.7|Storage Tests
C|M004.8|Storage Stabilization
C|M005|Repository Foundation
C|M005.1|Base Repository Model
C|M005.2|Local Repository
C|M005.3|Repository Validation
C|M005.4|Repository Metadata
C|M005.5|Repository Error Handling
C|M005.6|Repository Abstraction
C|M005.7|Repository Integration Tests
C|M005.8|Repository Stabilization
C|M006|Event Infrastructure
C|M006.1|Core Event Foundation
C|M006.1.1|Event Identity
C|M006.1.2|Event Metadata
C|M006.1.3|Event Payload Contracts
C|M006.1.4|Event Validation
C|M006.1.5|Event Serialization
C|M006.1.6|Event Exceptions
C|M006.1.7|Event Package Exports
C|M006.1.8|Core Event Tests
C|M006.2|Event Services Foundation
C|M006.2.1|Event Creation Service
C|M006.2.2|Event Validation Service
C|M006.2.3|Event Serialization Service
C|M006.2.4|Event Query Support
C|M006.2.5|Event Metadata Services
C|M006.2.6|Event Integration Tests
C|M006.2.7|Event Service Stabilization
C|M006.3|Event Repository Infrastructure
C|M006.3.1|Event Repository Contracts
C|M006.3.2|Event Repository Interface
C|M006.3.3|Base Event Repository
C|M006.3.4|Memory Event Repository
C|M006.3.5|Event Repository Metadata
C|M006.3.6|Event Repository Validation
C|M006.3.7|Event Repository Registry
C|M006.3.8|Event Repository Factory
C|M006.3.9|Event Repository Package Integration
C|M006.3.10|Event Repository Documentation
C|M006.3.11|Event Repository Unit Tests
C|M006.3.12|Event Repository Integration Tests
C|M006.3.13|Stabilization, Commit and Push
C|M007|Audit Infrastructure
C|M007.1|Audit Record Contracts
C|M007.2|Audit Event Model
C|M007.3|Actor and Source Metadata
C|M007.4|Audit Repository
C|M007.5|Audit Query Service
C|M007.6|Audit Integrity Validation
C|M007.7|Audit Export
C|M007.8|Audit API Contracts
C|M007.9|Audit Tests
C|M007.10|Audit Stabilization
C|M008|Master Registry Foundation
C|M008.1|Registry Contracts
C|M008.2|Registry Identifier Model
C|M008.3|Base Registry
C|M008.4|Registry Repository Interface
C|M008.5|Memory Registry Repository
C|M008.6|Registry Factory
C|M008.7|Registry Catalogue
C|M008.8|Registry Lifecycle
C|M008.9|Registry Validation
C|M008.10|Registry Events
C|M008.11|Registry APIs
C|M008.12|Registry Audit Integration
C|M008.13|Registry Tests
C|M008.14|Registry Stabilization
C|M008.15|Registry Metadata and Capability Contracts
C|M008.15.1|Registry Capability Model
C|M008.15.2|Data Classification Metadata
C|M008.15.3|Training Eligibility Metadata
C|M008.15.4|Provenance Metadata
C|M008.15.5|Retention Metadata
C|M008.15.6|Registry Metadata Validation
C|M008.15.7|Registry Metadata Tests
C|M008.16|Cross-Registry Relationship Foundation
C|M008.16.1|Relationship Contracts
C|M008.16.2|Immutable Reference Rules
C|M008.16.3|Relationship Direction
C|M008.16.4|Relationship Constraints
C|M008.16.5|Relationship Provenance
C|M008.16.6|Relationship APIs
C|M008.16.7|Relationship Tests
C|M008.17|Canonical Dataset Foundation
P|M009|Data Catalogue and Communication Foundations
C|M009.1|Name Catalogue
C|M009.1.1|First-Name Catalogue
C|M009.1.2|Middle-Name Catalogue
C|M009.1.3|Surname Catalogue
C|M009.1.4|Name Metadata
C|M009.1.5|Name Repository
C|M009.1.6|Name Search
C|M009.1.7|Name Catalogue Tests
P|M009.2|Name Suggestion Engine
C|M009.2.1|Manual Name Entry
C|M009.2.2|Single-Name Suggestions
C|M009.2.3|Pair Suggestions
C|M009.2.4|Trio Suggestions
C|M009.2.5|Full-Name Suggestions
C|M009.2.6|Name Normalization
C|M009.2.7|Duplicate Controls
C|M009.2.8|Suggestion APIs
C|M009.2.9|Suggestion Tests
P|M009.10|Name Catalogue Integration & Enrichment
C|M009.10.1|Sex-Usage Classification Contract
C|M009.10.2|Sex-Aware Name Compatibility
C|M009.10.3|PostgreSQL Name Repository Adapter
C|M009.10.4|PostgreSQL Name Catalogue Migration
C|M009.10.5|Local CSV Candidate Model
C|M009.10.6|CSV Name Import Staging
C|M009.10.7|Candidate Validation and Quarantine
C|M009.10.8|Controlled Name Batch Import
P|M009.10.9|Offline Name Catalogue Cache
P|M009.10.10|Name Catalogue Sync and Receipts
P|M009.10.11|Integration APIs
P|M009.10.12|Integration and Regression Tests
P|M009.3|Email Registry
P|M009.3.1|Email Address Model
P|M009.3.2|Email-Type Model
P|M009.3.3|Email Candidate Generation
P|M009.3.4|Availability Checking
P|M009.3.5|Atomic Reservation
P|M009.3.6|Assignment and Ownership
P|M009.3.7|Verification State
P|M009.3.8|Email Lifecycle
P|M009.3.9|Email Repository
P|M009.3.10|Email Events
P|M009.3.11|Email APIs
P|M009.3.12|Email Audit
P|M009.3.13|Email Registry Tests
P|M009.4|Simulation Mail Platform
P|M009.4.1|Mailbox Contracts
P|M009.4.2|Mailbox Provisioning
P|M009.4.3|Message Contracts
P|M009.4.4|Message Repository
P|M009.4.5|Inbox and Folder Model
P|M009.4.6|Threading and Replies
P|M009.4.7|Drafts and Sent Mail
P|M009.4.8|Read, Unread and Archive States
P|M009.4.9|Search and Filtering
P|M009.4.10|Mailbox Read Models
P|M009.4.11|Simulation Mail APIs
P|M009.4.12|Simulation Mail Tests
P|M009.5|Business Communication Engine
P|M009.5.1|Communication Policies
P|M009.5.2|Message Purpose Catalogue
P|M009.5.3|Template Families
P|M009.5.4|Context Variable Model
P|M009.5.5|Message Rendering
P|M009.5.6|Tone and Audience Rules
P|M009.5.7|Time and Urgency Rules
P|M009.5.8|Business Event Integration
P|M009.5.9|Communication Engine Tests
P|M009.6|Mail Delivery Gateway
P|M009.6.1|Delivery Provider Contracts
P|M009.6.2|Internal Simulation Delivery
P|M009.6.3|Zoho Mail Adapter
P|M009.6.4|Sender Identity Configuration
P|M009.6.5|Delivery Status Tracking
P|M009.6.6|Delivery Retry Handling
P|M009.6.7|Bounce and Failure Handling
P|M009.6.8|Delivery Audit
P|M009.6.9|Delivery Gateway Tests
P|M009.7|Communication Training Export
P|M009.7.1|Training Eligibility Metadata
P|M009.7.2|Dataset Provenance
P|M009.7.3|JSONL Export
P|M009.7.4|YAML Export
P|M009.7.5|Markdown Export
P|M009.7.6|Dataset Versioning
P|M009.7.7|Sensitive-Data Filtering
P|M009.7.8|Retention and Deletion Policies
P|M009.7.9|Training Export Tests
P|M009.8|Simulation Email Lifecycle
P|M009.8.1|Simulation Email Accounts
P|M009.8.2|Email Promotion Workflow
P|M009.8.3|Email Verification Lifecycle
P|M009.8.4|Email History Preservation
P|M009.8.5|Production Email Activation
P|M009.8.6|Email Lifecycle Tests
P|M009.9|Geography and Community Catalogue
P|M009.9.1|Country Registry
P|M009.9.2|Province and State Registry
P|M009.9.3|District Registry
P|M009.9.4|Ward Registry
P|M009.9.5|Village and Locality Registry
P|M009.9.6|Estate and Neighbourhood Registry
P|M009.9.7|Address and Place Reference Model
P|M009.9.8|Road and Route Catalogue
P|M009.9.9|Market and Trading-Centre Catalogue
P|M009.9.10|Public-Facility Location Catalogue
P|M009.9.11|Geographic Hierarchy Validation
P|M009.9.12|Geography Events
P|M009.9.13|Geography APIs
P|M009.9.14|Geography Tests
P|M010|National Identity Platform
P|M010.1|Birth Registry
P|M010.1.1|Birth Reference Contracts
P|M010.1.2|Birth Reference Generator
P|M010.1.3|Available Reference Pool
P|M010.1.4|Birth Registration Records
P|M010.1.5|Birth Registry Repository
P|M010.1.6|Birth Registry Events
P|M010.1.7|Birth Registry APIs
P|M010.1.8|Birth Registry Tests
P|M010.2|Citizen Registry
P|M010.2.1|Citizen Contracts
P|M010.2.2|Structured Name Model
P|M010.2.3|Citizen Identity Generator
P|M010.2.4|Birth-to-Citizen Linking
P|M010.2.5|Citizen Repository
P|M010.2.6|Citizen Lifecycle
P|M010.2.7|Citizen Events
P|M010.2.8|Citizen APIs
P|M010.2.9|Citizen Tests
P|M010.3|National ID Registry
P|M010.3.1|National ID Contracts
P|M010.3.2|National ID Generator
P|M010.3.3|National ID Assignment
P|M010.3.4|Citizen Ownership Linking
P|M010.3.5|National ID Repository
P|M010.3.6|National ID Lifecycle
P|M010.3.7|National ID Events
P|M010.3.8|National ID APIs
P|M010.3.9|National ID Tests
P|M010.4|NexaID Registry
P|M010.4.1|NexaID Contracts
P|M010.4.2|Collaborative NexaID Generation
P|M010.4.3|Provider Contribution
P|M010.4.4|Client Contribution
P|M010.4.5|Citizen Contribution
P|M010.4.6|Timestamp and Nonce
P|M010.4.7|NexaID Repository
P|M010.4.8|NexaID Lifecycle
P|M010.4.9|NexaID Events
P|M010.4.10|NexaID APIs
P|M010.4.11|NexaID Tests
P|M010.5|Citizen Identity Promotion
P|M010.5.1|Simulation Citizen Review
P|M010.5.2|Citizen Approval Workflow
P|M010.5.3|Production Citizen Activation
P|M010.5.4|Citizen History Preservation
P|M010.5.5|Identity Promotion Audit
P|M010.5.6|Identity Promotion Tests
P|M010.6|Citizen Identity Assets
P|M010.6.1|Profile Picture Assignment
P|M010.6.2|Avatar Generation Provider
P|M010.6.3|Citizen ID Card Rendering
P|M010.6.4|Secure Identity Storage
P|M010.6.5|Identity Document Delivery
P|M010.6.6|Identity Asset Tests
P|M010.7|Civil Registration and Birth Provenance
P|M010.7.1|Pregnancy Record Contracts
P|M010.7.2|Healthcare Facility Registry Link
P|M010.7.3|Birth Attendant Registry Link
P|M010.7.4|Hospital Birth Event
P|M010.7.5|Home Birth Event
P|M010.7.6|Late Birth Registration
P|M010.7.7|Birth Verification Workflow
P|M010.7.8|Birth Certificate Issuance
P|M010.7.9|Birth Certificate Amendment by Event
P|M010.7.10|Birth Certificate Lifecycle
P|M010.7.11|Civil Registration Audit
P|M010.7.12|Civil Registration Tests
P|M010.8|Household and Family Relationships
P|M010.8.1|Household Contracts
P|M010.8.2|Household Identifier Generator
P|M010.8.3|Parent-to-Child Relationships
P|M010.8.4|Guardian Relationships
P|M010.8.5|Dependant Relationships
P|M010.8.6|Spouse and Partner Relationships
P|M010.8.7|Household Membership Lifecycle
P|M010.8.8|Household Residence Linking
P|M010.8.9|Household Events
P|M010.8.10|Household APIs
P|M010.8.11|Household Tests
P|M010.9|Citizen Life Status Foundation
P|M010.9.1|Life Status Contracts
P|M010.9.2|Minor and Adult Status Derivation
P|M010.9.3|Marriage Registration Link
P|M010.9.4|Retirement Status Link
P|M010.9.5|Death Registration
P|M010.9.6|Deceased Identity Protection
P|M010.9.7|Estate and Inheritance Reference Foundation
P|M010.9.8|Life Status Events
P|M010.9.9|Life Status APIs
P|M010.9.10|Life Status Tests
P|M011|Telecommunications Platform
P|M011.1|NexaCom Number Registry
P|M011.1.1|Number Contracts
P|M011.1.2|Number Range Configuration
P|M011.1.3|Number Pool Generator
P|M011.1.4|Available Number Pool
P|M011.1.5|Number Reservation
P|M011.1.6|Number Assignment
P|M011.1.7|Number Ownership
P|M011.1.8|Number Lifecycle
P|M011.1.9|Number Repository
P|M011.1.10|Number Events
P|M011.1.11|Number APIs
P|M011.1.12|Number Registry Tests
P|M011.2|SIM Registry
P|M011.2.1|SIM Contracts
P|M011.2.2|SIM Serial Generator
P|M011.2.3|Unregistered SIM Pool
P|M011.2.4|SIM Reservation
P|M011.2.5|SIM Registration
P|M011.2.6|Number-to-SIM Linking
P|M011.2.7|Citizen-to-SIM Linking
P|M011.2.8|SIM Lifecycle
P|M011.2.9|SIM Repository
P|M011.2.10|SIM Events
P|M011.2.11|SIM APIs
P|M011.2.12|SIM Tests
P|M011.3|Telecommunication Usage and Communication Behaviour
P|M011.3.1|Communication Preference Contracts
P|M011.3.2|Preferred Contact Method
P|M011.3.3|Language Preference
P|M011.3.4|Number Usage History
P|M011.3.5|SIM Usage History
P|M011.3.6|Communication Availability State
P|M011.3.7|Communication Reputation Signals
P|M011.3.8|Usage Events
P|M011.3.9|Usage APIs
P|M011.3.10|Usage Tests
P|M012|Financial Identity, Banking and Payment Infrastructure
P|M012.1|NRA Registry
P|M012.1.1|NRA PIN Contracts
P|M012.1.2|NRA PIN Generator
P|M012.1.3|Email Requirement Policy
P|M012.1.4|Citizen Registration
P|M012.1.5|NRA Repository
P|M012.1.6|NRA Lifecycle
P|M012.1.7|NRA Events
P|M012.1.8|NRA APIs
P|M012.1.9|NRA Email Communications
P|M012.1.10|NRA Tests
P|M012.2|NeHIF Registry
P|M012.2.1|NeHIF Contracts
P|M012.2.2|Membership Number Generator
P|M012.2.3|Email Requirement Policy
P|M012.2.4|Citizen Registration
P|M012.2.5|NeHIF Repository
P|M012.2.6|Contribution Records
P|M012.2.7|NeHIF Events
P|M012.2.8|NeHIF APIs
P|M012.2.9|NeHIF Email Communications
P|M012.2.10|NeHIF Tests
P|M012.3|Financial Institution and Payment-Network Foundation
P|M012.3.1|Financial Institution Registry
P|M012.3.1.1|Financial Institution Contracts
P|M012.3.1.2|Institution Identifier Generator
P|M012.3.1.3|Institution Registration
P|M012.3.1.4|Institution Status
P|M012.3.1.5|Institution Repository
P|M012.3.1.6|Institution Lifecycle
P|M012.3.1.7|Institution Events
P|M012.3.1.8|Institution APIs
P|M012.3.1.9|Institution Tests
P|M012.3.2|Payment Network Registry
P|M012.3.2.1|Payment Network Contracts
P|M012.3.2.2|Visa Network Registration
P|M012.3.2.3|Mastercard Network Registration
P|M012.3.2.4|Verve Network Registration
P|M012.3.2.5|RuPay Network Registration
P|M012.3.2.6|UnionPay Network Registration
P|M012.3.2.7|American Express Network Registration
P|M012.3.2.8|Discover Network Registration
P|M012.3.2.9|Domestic Network Registration
P|M012.3.2.10|Network Status and Availability
P|M012.3.2.11|Network Repository
P|M012.3.2.12|Network Events
P|M012.3.2.13|Network APIs
P|M012.3.2.14|Network Tests
P|M012.3.3|BIN Registry
P|M012.3.3.1|BIN Contracts
P|M012.3.3.2|BIN Range Model
P|M012.3.3.3|BIN Registration
P|M012.3.3.4|BIN-to-Institution Linking
P|M012.3.3.5|BIN-to-Network Linking
P|M012.3.3.6|BIN Country Metadata
P|M012.3.3.7|BIN Currency Metadata
P|M012.3.3.8|BIN Card-Format Metadata
P|M012.3.3.9|BIN Status
P|M012.3.3.10|BIN Lookup
P|M012.3.3.11|BIN Repository
P|M012.3.3.12|BIN Events
P|M012.3.3.13|BIN APIs
P|M012.3.3.14|BIN Tests
P|M012.3.4|Card-Format Policy Registry
P|M012.3.4.1|Card-Format Contracts
P|M012.3.4.2|PAN Length Rules
P|M012.3.4.3|PAN Prefix Rules
P|M012.3.4.4|PAN Check-Digit Rules
P|M012.3.4.5|Card Display-Masking Rules
P|M012.3.4.6|Expiry-Period Rules
P|M012.3.4.7|CVV/CVC Length Rules
P|M012.3.4.8|PIN-Length Rules
P|M012.3.4.9|NFC-Authorization Rules
P|M012.3.4.10|EMV Metadata Rules
P|M012.3.4.11|Card-Format Repository
P|M012.3.4.12|Card-Format Tests
P|M012.3.5|Banking Product-Limit Policy
P|M012.3.5.1|Maximum Three Account Types per Bank
P|M012.3.5.2|Maximum Three Card Types per Bank
P|M012.3.5.3|Bank-Specific Account-Type Registration
P|M012.3.5.4|Bank-Specific Card-Type Registration
P|M012.3.5.5|Product-Limit Validation
P|M012.3.5.6|Product-Limit Policy Tests
P|M012.4|Banking Foundation
P|M012.4.1|Bank Registry
P|M012.4.1.1|Bank Contracts
P|M012.4.1.2|Bank Registration
P|M012.4.1.3|Bank-to-Institution Linking
P|M012.4.1.4|Bank BIN Allocation
P|M012.4.1.5|Bank Payment-Network Enrollment
P|M012.4.1.6|Bank Status
P|M012.4.1.7|Bank Repository
P|M012.4.1.8|Bank Events
P|M012.4.1.9|Bank APIs
P|M012.4.1.10|Bank Tests
P|M012.4.2|Branch Registry
P|M012.4.2.1|Branch Contracts
P|M012.4.2.2|Branch Identifier Generator
P|M012.4.2.3|Branch Registration
P|M012.4.2.4|Bank-to-Branch Linking
P|M012.4.2.5|Branch Repository
P|M012.4.2.6|Branch Lifecycle
P|M012.4.2.7|Branch Events
P|M012.4.2.8|Branch APIs
P|M012.4.2.9|Branch Tests
P|M012.4.3|Bank Account-Type Registry
P|M012.4.3.1|Account-Type Contracts
P|M012.4.3.2|Account-Type Registration
P|M012.4.3.3|Three-Type Limit Enforcement
P|M012.4.3.4|Account-Type Eligibility Rules
P|M012.4.3.5|Account-Type Status
P|M012.4.3.6|Account-Type Repository
P|M012.4.3.7|Account-Type Tests
P|M012.4.4|Bank Account Registry
P|M012.4.4.1|Account Contracts
P|M012.4.4.2|Account Number Generator
P|M012.4.4.3|Email Requirement Policy
P|M012.4.4.4|Account Application
P|M012.4.4.5|Account Approval
P|M012.4.4.6|Account Rejection
P|M012.4.4.7|Citizen-to-Account Linking
P|M012.4.4.8|Business-to-Account Linking
P|M012.4.4.9|Branch-to-Account Linking
P|M012.4.4.10|Account Repository
P|M012.4.4.11|Account Lifecycle
P|M012.4.4.12|Account Events
P|M012.4.4.13|Account APIs
P|M012.4.4.14|Account Communications
P|M012.4.4.15|Account Tests
P|M012.4.5|Bank Account Balance Model
P|M012.4.5.1|Balance Contracts
P|M012.4.5.2|Ledger Balance
P|M012.4.5.3|Current Balance
P|M012.4.5.4|Available Balance
P|M012.4.5.5|Pending Settlement Balance
P|M012.4.5.6|Held and Reserved Balance
P|M012.4.5.7|Balance Derivation Rules
P|M012.4.5.8|Balance Read Models
P|M012.4.5.9|Balance APIs
P|M012.4.5.10|Balance Tests
P|M012.5|Bank Card Registry
P|M012.5.1|Bank Card-Type Registry
P|M012.5.1.1|Card-Type Contracts
P|M012.5.1.2|Bank-Specific Card-Type Registration
P|M012.5.1.3|Three-Type Limit Enforcement
P|M012.5.1.4|Card-Type BIN Assignment
P|M012.5.1.5|Card-Type Network Assignment
P|M012.5.1.6|Card-Type Expiry Policy
P|M012.5.1.7|Card-Type PIN Policy
P|M012.5.1.8|Card-Type NFC Policy
P|M012.5.1.9|Card-Type Repository
P|M012.5.1.10|Card-Type Tests
P|M012.5.2|Card Number Generation
P|M012.5.2.1|PAN Generator Contracts
P|M012.5.2.2|BIN-Based PAN Generation
P|M012.5.2.3|PAN Check-Digit Generation
P|M012.5.2.4|PAN Uniqueness Validation
P|M012.5.2.5|PAN Reservation
P|M012.5.2.6|Masked PAN Representation
P|M012.5.2.7|PAN Generator Tests
P|M012.5.3|Card Expiry Generation
P|M012.5.3.1|Expiry Contracts
P|M012.5.3.2|Issue-Date Capture
P|M012.5.3.3|Bank Expiry-Period Policy
P|M012.5.3.4|Expiry Month Generation
P|M012.5.3.5|Expiry Year Generation
P|M012.5.3.6|VALID THRU Formatting
P|M012.5.3.7|Expiry Validation
P|M012.5.3.8|Expiry Generator Tests
P|M012.5.4|CVV/CVC Generation
P|M012.5.4.1|CVV/CVC Contracts
P|M012.5.4.2|Security-Policy Selection
P|M012.5.4.3|Deterministic Simulation Generation
P|M012.5.4.4|Secure Storage Representation
P|M012.5.4.5|Verification Interface
P|M012.5.4.6|CVV/CVC Generator Tests
P|M012.5.5|Card Issuance
P|M012.5.5.1|Card Issuance Contracts
P|M012.5.5.2|Automatic Issuance Policy
P|M012.5.5.3|Manual Issuance Policy
P|M012.5.5.4|Account-to-Card Linking
P|M012.5.5.5|Cardholder Linking
P|M012.5.5.6|Multiple Cards per Account
P|M012.5.5.7|Card Replacement
P|M012.5.5.8|Card Reissuance
P|M012.5.5.9|Card Issuance Events
P|M012.5.5.10|Card Issuance Tests
P|M012.5.6|Card Activation and Verification
P|M012.5.6.1|Card Activation Contracts
P|M012.5.6.2|Automatic Verification Policy
P|M012.5.6.3|Manual Verification Policy
P|M012.5.6.4|Immediate Activation Policy
P|M012.5.6.5|Deferred Activation Policy
P|M012.5.6.6|First-Use Activation Policy
P|M012.5.6.7|Activation Events
P|M012.5.6.8|Activation Tests
P|M012.5.7|PIN Policy Engine
P|M012.5.7.1|PIN Contracts
P|M012.5.7.2|PIN Setup Before Transactions
P|M012.5.7.3|PIN Setup on First Use
P|M012.5.7.4|Initial PIN Replacement
P|M012.5.7.5|PIN Verification
P|M012.5.7.6|PIN Attempt Limits
P|M012.5.7.7|PIN Blocking State
P|M012.5.7.8|PIN Reset
P|M012.5.7.9|PIN Events
P|M012.5.7.10|PIN Tests
P|M012.5.8|NFC and EMV Simulation
P|M012.5.8.1|EMV Simulation Contracts
P|M012.5.8.2|Chip-Presented Simulation
P|M012.5.8.3|NFC Authorization Simulation
P|M012.5.8.4|Contactless Eligibility
P|M012.5.8.5|Contactless Limit Policy
P|M012.5.8.6|PIN Fallback
P|M012.5.8.7|Terminal Capability Validation
P|M012.5.8.8|EMV Authorization Events
P|M012.5.8.9|NFC Authorization Events
P|M012.5.8.10|EMV and NFC Tests
P|M012.5.9|Card Lifecycle and Repository
P|M012.5.9.1|Card Status Registry
P|M012.5.9.2|Issued State
P|M012.5.9.3|Active State
P|M012.5.9.4|Blocked State
P|M012.5.9.5|Expired State
P|M012.5.9.6|Replaced State
P|M012.5.9.7|Closed State
P|M012.5.9.8|Card Repository
P|M012.5.9.9|Card Events
P|M012.5.9.10|Card APIs
P|M012.5.9.11|Card Audit
P|M012.5.9.12|Card Registry Tests
P|M012.6|Payment Authorization and Settlement Platform
P|M012.6.1|Payment Event Contracts
P|M012.6.1.1|Payment Initiated Event
P|M012.6.1.2|Payment Authorization Requested Event
P|M012.6.1.3|Payment Authorized Event
P|M012.6.1.4|Payment Declined Event
P|M012.6.1.5|Payment Captured Event
P|M012.6.1.6|Payment Settled Event
P|M012.6.1.7|Payment Failed Event
P|M012.6.1.8|Payment Reversed Event
P|M012.6.1.9|Balance Updated Event
P|M012.6.1.10|Receipt Issued Event
P|M012.6.1.11|Payment Event Tests
P|M012.6.2|Payment Authorization Engine
P|M012.6.2.1|Authorization Contracts
P|M012.6.2.2|Customer Account Validation
P|M012.6.2.3|Card Status Validation
P|M012.6.2.4|Expiry Validation
P|M012.6.2.5|CVV/CVC Verification
P|M012.6.2.6|PIN Verification
P|M012.6.2.7|NFC Authorization
P|M012.6.2.8|Available-Balance Validation
P|M012.6.2.9|Authorization Hold
P|M012.6.2.10|Approval and Decline Rules
P|M012.6.2.11|Authorization APIs
P|M012.6.2.12|Authorization Tests
P|M012.6.3|Settlement Policy Registry
P|M012.6.3.1|Settlement Policy Contracts
P|M012.6.3.2|Payment-Rail Settlement Policy
P|M012.6.3.3|Bank Settlement Policy
P|M012.6.3.4|Immediate Settlement Policy
P|M012.6.3.5|Same-Day Settlement Policy
P|M012.6.3.6|T+1 Settlement Policy
P|M012.6.3.7|T+2 Settlement Policy
P|M012.6.3.8|Business-Day Calendar Rules
P|M012.6.3.9|Weekend and Holiday Rules
P|M012.6.3.10|Settlement Policy Repository
P|M012.6.3.11|Settlement Policy APIs
P|M012.6.3.12|Settlement Policy Tests
P|M012.6.4|Payment Fee Registry
P|M012.6.4.1|Fee Contracts
P|M012.6.4.2|A2A Flat-Fee Policy
P|M012.6.4.3|Interchange Fee Policy
P|M012.6.4.4|Payment-Network Fee Policy
P|M012.6.4.5|Acquirer Fee Policy
P|M012.6.4.6|Fixed and Percentage Fees
P|M012.6.4.7|Fee Calculation
P|M012.6.4.8|Gross Settlement Amount
P|M012.6.4.9|Net Settlement Amount
P|M012.6.4.10|Fee Repository
P|M012.6.4.11|Fee APIs
P|M012.6.4.12|Fee Tests
P|M012.6.5|A2A Payment Rail
P|M012.6.5.1|A2A Contracts
P|M012.6.5.2|Customer Account Selection
P|M012.6.5.3|Merchant Account Selection
P|M012.6.5.4|A2A Authorization
P|M012.6.5.5|Immediate Funds Transfer
P|M012.6.5.6|Upfront Fee Deduction
P|M012.6.5.7|Immediate Merchant Credit
P|M012.6.5.8|Immediate Available-Balance Update
P|M012.6.5.9|Final Payment State
P|M012.6.5.10|A2A Receipt
P|M012.6.5.11|A2A Events
P|M012.6.5.12|A2A APIs
P|M012.6.5.13|A2A Tests
P|M012.6.6|EMV Card Payment Rail
P|M012.6.6.1|EMV Payment Contracts
P|M012.6.6.2|Card-Present Transaction
P|M012.6.6.3|Network Selection by BIN
P|M012.6.6.4|Issuing-Bank Authorization
P|M012.6.6.5|Acquiring-Bank Routing
P|M012.6.6.6|Authorization Hold
P|M012.6.6.7|Payment Capture
P|M012.6.6.8|Pending Settlement Creation
P|M012.6.6.9|EMV Receipt
P|M012.6.6.10|EMV Events
P|M012.6.6.11|EMV APIs
P|M012.6.6.12|EMV Tests
P|M012.6.7|EMV Batch and Settlement Engine
P|M012.6.7.1|Settlement Batch Contracts
P|M012.6.7.2|Transaction Capture Queue
P|M012.6.7.3|Daily Batch Creation
P|M012.6.7.4|Batch Cut-Off Policy
P|M012.6.7.5|Network Settlement
P|M012.6.7.6|Acquirer Settlement
P|M012.6.7.7|Fee Netting
P|M012.6.7.8|Merchant Settlement
P|M012.6.7.9|Pending-Balance Release
P|M012.6.7.10|Available-Balance Credit
P|M012.6.7.11|Settlement Failure Handling
P|M012.6.7.12|Settlement Retry
P|M012.6.7.13|Settlement Events
P|M012.6.7.14|Settlement Tests
P|M012.6.8|Payment-Rail Availability and Fallback
P|M012.6.8.1|Rail Availability Contracts
P|M012.6.8.2|Payment-Network Health State
P|M012.6.8.3|Terminal Availability State
P|M012.6.8.4|Terminal Maintenance State
P|M012.6.8.5|EMV-Unavailable Detection
P|M012.6.8.6|A2A Fallback Eligibility
P|M012.6.8.7|Customer Fallback Confirmation
P|M012.6.8.8|Merchant Fallback Confirmation
P|M012.6.8.9|Fallback Reason Logging
P|M012.6.8.10|Fallback Audit
P|M012.6.8.11|Fallback Tests
P|M012.6.9|Chargeback, Hold and Reserve Simulation
P|M012.6.9.1|Chargeback Contracts
P|M012.6.9.2|EMV Chargeback Eligibility
P|M012.6.9.3|A2A Finality Policy
P|M012.6.9.4|Merchant Hold Policy
P|M012.6.9.5|Rolling Reserve Policy
P|M012.6.9.6|Funds Hold
P|M012.6.9.7|Funds Release
P|M012.6.9.8|Funds Clawback
P|M012.6.9.9|Chargeback Events
P|M012.6.9.10|Chargeback Tests
P|M012.6.10|Merchant Settlement Read Models
P|M012.6.10.1|Gross Sales Read Model
P|M012.6.10.2|A2A Available-Funds Read Model
P|M012.6.10.3|EMV Pending-Settlement Read Model
P|M012.6.10.4|Processing-Fees Read Model
P|M012.6.10.5|Net Settlement Read Model
P|M012.6.10.6|Settlement-Date Projection
P|M012.6.10.7|Held-Funds Read Model
P|M012.6.10.8|Merchant Liquidity Read Model
P|M012.6.10.9|Settlement Dashboard APIs
P|M012.6.10.10|Settlement Read-Model Tests
P|M012.6.11|Multi-Client Transaction Sessions
P|M012.6.11.1|Payment Session Contracts
P|M012.6.11.2|Merchant-Side Session
P|M012.6.11.3|Customer-Side Session
P|M012.6.11.4|Shared Transaction Identifier
P|M012.6.11.5|Real-Time Session Synchronization
P|M012.6.11.6|Customer Authorization Prompt
P|M012.6.11.7|Merchant Payment-State Display
P|M012.6.11.8|Session Timeout
P|M012.6.11.9|Session Cancellation
P|M012.6.11.10|Session Audit
P|M012.6.11.11|Multi-Client Session APIs
P|M012.6.11.12|Multi-Client Session Tests
P|M012.6.12|Payment Simulation and Verification
P|M012.6.12.1|Simulation Payment Contracts
P|M012.6.12.2|Automated NFC Authorization Events
P|M012.6.12.3|Automated PIN Authorization Events
P|M012.6.12.4|Manual Tester PIN Flow
P|M012.6.12.5|Manual Tester NFC Flow
P|M012.6.12.6|Simulated A2A Flow
P|M012.6.12.7|Simulated EMV Flow
P|M012.6.12.8|Manual-versus-Simulated Event Comparison
P|M012.6.12.9|Ledger-Outcome Comparison
P|M012.6.12.10|Settlement-Outcome Comparison
P|M012.6.12.11|Payment Simulation APIs
P|M012.6.12.12|Payment Simulation Tests
P|M012.6.13|Payment Platform Audit and Stabilization
P|M012.6.13.1|Payment Audit Trail
P|M012.6.13.2|Authorization Audit
P|M012.6.13.3|Settlement Audit
P|M012.6.13.4|Fee Audit
P|M012.6.13.5|Balance Reconciliation
P|M012.6.13.6|Payment Integrity Verification
P|M012.6.13.7|Full Payment Test Suite
P|M012.6.13.8|Payment Platform Stabilization
P|M012.7|NexaPesa Registry
P|M012.7.1|Wallet Contracts
P|M012.7.2|Wallet Number Generator
P|M012.7.3|Phone-to-Wallet Linking
P|M012.7.4|Citizen-to-Wallet Linking
P|M012.7.5|Wallet Registration
P|M012.7.6|Wallet Repository
P|M012.7.7|Wallet Lifecycle
P|M012.7.8|Wallet Balance Model
P|M012.7.9|Wallet Events
P|M012.7.10|Wallet APIs
P|M012.7.11|Wallet Communications
P|M012.7.12|Wallet Tests
P|M012.8|Payment Execution Modes
P|M012.8.1|Simulation Payment Rules
P|M012.8.2|Production Payment Rules
P|M012.8.3|Tap-Only Simulation Policy
P|M012.8.4|PIN Authorization Policy
P|M012.8.5|Payment Capability Resolution
P|M012.8.6|Payment Mode Tests
P|M012.9|Central Monetary Authority
P|M012.9.1|Monetary Authority Contracts
P|M012.9.2|Currency Registry
P|M012.9.3|Currency Issuance and Withdrawal
P|M012.9.4|Commercial Bank Licensing
P|M012.9.5|Reserve Requirement Policy
P|M012.9.6|Policy Interest Rate
P|M012.9.7|Inflation Observation Model
P|M012.9.8|Interbank Settlement Foundation
P|M012.9.9|Cash Circulation Model
P|M012.9.10|Digital Currency Foundation
P|M012.9.11|Monetary Policy Events
P|M012.9.12|Monetary Authority APIs
P|M012.9.13|Monetary Authority Audit
P|M012.9.14|Monetary Authority Tests
P|M012.10|Credit, Insurance and Long-Term Finance Foundation
P|M012.10.1|Credit Bureau Registry
P|M012.10.2|Loan Product Registry
P|M012.10.3|Loan Application Lifecycle
P|M012.10.4|Credit Assessment Contracts
P|M012.10.5|Insurance Institution Registry
P|M012.10.6|Insurance Product Registry
P|M012.10.7|Policy and Claim Lifecycle
P|M012.10.8|Pension Fund Registry
P|M012.10.9|Pension Contribution Lifecycle
P|M012.10.10|Long-Term Finance Events
P|M012.10.11|Long-Term Finance Tests
P|M013|Business and Employment Registries
P|M013.1|Business Registry
P|M013.1.1|Business Contracts
P|M013.1.2|Business Registration Number Generator
P|M013.1.3|Business Ownership
P|M013.1.4|Business Repository
P|M013.1.5|Business Lifecycle
P|M013.1.6|Business Events
P|M013.1.7|Business APIs
P|M013.1.8|Business Tests
P|M013.2|Employer Registry
P|M013.2.1|Employer Contracts
P|M013.2.2|Employer ID Generator
P|M013.2.3|Business-to-Employer Linking
P|M013.2.4|Employer Repository
P|M013.2.5|Employer Lifecycle
P|M013.2.6|Employer Events
P|M013.2.7|Employer APIs
P|M013.2.8|Employer Tests
P|M013.3|Employee Registry
P|M013.3.1|Employee Contracts
P|M013.3.2|Employee Number Generator
P|M013.3.3|Citizen-to-Employee Linking
P|M013.3.4|Employer-to-Employee Linking
P|M013.3.5|Employment Profile
P|M013.3.6|Employee Repository
P|M013.3.7|Employment Lifecycle
P|M013.3.8|Employment Events
P|M013.3.9|Employment APIs
P|M013.3.10|Employment Communications
P|M013.3.11|Employee Tests
P|M013.4|Merchant Identifier Registry
P|M013.4.1|Merchant Contracts
P|M013.4.2|Merchant Number Generator
P|M013.4.3|Till Number Generator
P|M013.4.4|Paybill Number Generator
P|M013.4.5|Business Ownership Linking
P|M013.4.6|Merchant Repository
P|M013.4.7|Merchant Lifecycle
P|M013.4.8|Merchant Events
P|M013.4.9|Merchant APIs
P|M013.4.10|Merchant Tests
P|M013.5|Business Type and Economic-Actor Foundation
P|M013.5.1|Business Type Contracts
P|M013.5.2|Sole Trader Model
P|M013.5.3|Partnership Model
P|M013.5.4|Company Model
P|M013.5.5|Cooperative Model
P|M013.5.6|Non-Governmental Organisation Model
P|M013.5.7|Informal Business Model
P|M013.5.8|Home Business Model
P|M013.5.9|Street Vendor Model
P|M013.5.10|Farmer and Producer Model
P|M013.5.11|Manufacturer Model
P|M013.5.12|Wholesaler and Distributor Model
P|M013.5.13|Importer and Exporter Model
P|M013.5.14|Seasonal Business Model
P|M013.5.15|Business Type Validation
P|M013.5.16|Business Type Tests
P|M013.6|Employment Marketplace
P|M013.6.1|Vacancy Registry
P|M013.6.2|Job Requirement Contracts
P|M013.6.3|Verified Citizen CV Profile
P|M013.6.4|CV Compilation from Verified History
P|M013.6.5|Citizen CV Review
P|M013.6.6|Job Discovery and Notification
P|M013.6.7|Citizen Application Decision
P|M013.6.8|Job Application Submission
P|M013.6.9|Shortlisting
P|M013.6.10|Interview Lifecycle
P|M013.6.11|Employment Offer
P|M013.6.12|Offer Acceptance and Rejection
P|M013.6.13|Employment Onboarding
P|M013.6.14|Promotion and Transfer
P|M013.6.15|Resignation and Termination
P|M013.6.16|Retirement from Employment
P|M013.6.17|Employment Marketplace Events
P|M013.6.18|Employment Marketplace APIs
P|M013.6.19|Employment Marketplace Tests
P|M014|Device Registry Platform
P|M014.1|Device Contracts
P|M014.2|Device ID Generator
P|M014.3|Device Registration
P|M014.4|Device Ownership
P|M014.5|Device Trust State
P|M014.6|Device Lifecycle
P|M014.7|Device Repository
P|M014.8|Device Events
P|M014.9|Device APIs
P|M014.10|Device Audit
P|M014.11|Device Tests
P|M015|Provider Gateway
P|M015.1|Gateway Contracts
P|M015.2|Provider Registration
P|M015.3|Client Registration
P|M015.4|Registry Routing
P|M015.5|Request Validation
P|M015.6|Authorization Boundaries
P|M015.7|Idempotency
P|M015.8|Rate Limiting
P|M015.9|Error Contracts
P|M015.10|Gateway Events
P|M015.11|Gateway Audit
P|M015.12|Gateway APIs
P|M015.13|Gateway Tests
P|M015.14|Gateway Stabilization
P|M015.15|Runtime Execution Context
P|M015.15.1|Runtime State Resolution (Online/Offline)
P|M015.15.2|Environment Resolution (Simulation/Production)
P|M015.15.3|Execution Authority Resolution
P|M015.15.4|Runtime Validation
P|M015.15.5|Runtime Context APIs
P|M015.15.6|Runtime Context Tests
P|M016|Simulation Engine Foundation
P|M016.1|Simulation Contracts
P|M016.2|Simulation Scenario Model
P|M016.3|Simulation Runtime
P|M016.4|Registry-Owned Generators
P|M016.5|Scenario Seed Management
P|M016.6|Deterministic Generation
P|M016.7|Simulation Event Stream
P|M016.8|Simulation State
P|M016.9|Simulation Repository
P|M016.10|Simulation Export
P|M016.11|Simulation Audit
P|M016.12|Simulation APIs
P|M016.13|Simulation Tests
P|M016.14|AI Simulation Orchestration
P|M016.14.1|AI Scenario Generator
P|M016.14.2|AI Actor Behaviour
P|M016.14.3|AI Business Workflow Simulation
P|M016.14.4|AI Payment Simulation
P|M016.14.5|AI Citizen Simulation
P|M016.14.6|AI Failure Scenario Simulation
P|M016.14.7|AI Simulation Audit
P|M016.14.8|AI Simulation Tests
P|M016.15|Simulation Promotion Engine
P|M016.15.1|Promotion Eligibility
P|M016.15.2|Human Review Queue
P|M016.15.3|Promotion Approval
P|M016.15.4|Promotion Rejection
P|M016.15.5|Simulation Lineage Preservation
P|M016.15.6|Promotion Audit
P|M016.15.7|Promotion Tests
P|M016.16|Simulation Communication Platform
P|M016.16.1|Simulation Email Delivery
P|M016.16.2|Waiting Period Management
P|M016.16.3|Verification Notifications
P|M016.16.4|Reminder Scheduling
P|M016.16.5|Simulation Inbox Synchronization
P|M016.16.6|Communication Audit
P|M016.16.7|Communication Tests
P|M016.17|Autonomous Error Simulation
P|M016.17.1|Invalid Event Generation
P|M016.17.2|Invalid Payment Simulation
P|M016.17.3|Invalid Identity Simulation
P|M016.17.4|Invalid Banking Scenario Simulation
P|M016.17.5|Invalid Supply Chain Simulation
P|M016.17.6|Recovery Scenario Simulation
P|M016.17.7|Error Simulation Analytics
P|M016.17.8|Error Simulation Tests
P|M016.18|Citizen Behaviour Engine
P|M016.18.1|Needs and Wants Model
P|M016.18.2|Citizen Goal Model
P|M016.18.3|Preference Model
P|M016.18.4|Memory and Knowledge Model
P|M016.18.5|Habit Formation and Change
P|M016.18.6|Budgeting Behaviour
P|M016.18.7|Shopping Behaviour
P|M016.18.8|Saving Behaviour
P|M016.18.9|Borrowing Behaviour
P|M016.18.10|Investment Behaviour
P|M016.18.11|Learning and Skill Development
P|M016.18.12|Citizen Decision Audit
P|M016.18.13|Citizen Behaviour Tests
P|M016.19|Household Simulation
P|M016.19.1|Household Budget
P|M016.19.2|Household Shopping List
P|M016.19.3|Rent and Housing Costs
P|M016.19.4|Utilities and Household Services
P|M016.19.5|Household Asset Ownership
P|M016.19.6|Household Income Pooling
P|M016.19.7|Household Dependency Costs
P|M016.19.8|Household Decision Events
P|M016.19.9|Household Simulation Tests
P|M016.20|Business Behaviour Engine
P|M016.20.1|Business Goal Model
P|M016.20.2|Hiring Behaviour
P|M016.20.3|Pricing Behaviour
P|M016.20.4|Inventory Replenishment Behaviour
P|M016.20.5|Marketing Behaviour
P|M016.20.6|Competition Response
P|M016.20.7|Expansion and Relocation
P|M016.20.8|Partnership Formation
P|M016.20.9|Distress and Bankruptcy
P|M016.20.10|Business Behaviour Events
P|M016.20.11|Business Behaviour Tests
P|M016.21|Economic Behaviour Engine
P|M016.21.1|Supply and Demand Model
P|M016.21.2|Price Response Model
P|M016.21.3|Consumer Confidence Model
P|M016.21.4|Employment-Market Response
P|M016.21.5|Interest-Rate Response
P|M016.21.6|Inflation Response
P|M016.21.7|Seasonality
P|M016.21.8|Economic Shock Scenarios
P|M016.21.9|Economic Behaviour Events
P|M016.21.10|Economic Behaviour Tests
P|M016.22|Society and Social Influence Simulation
P|M016.22.1|Friendship Relationships
P|M016.22.2|Neighbour Relationships
P|M016.22.3|Community Group Relationships
P|M016.22.4|Social Learning
P|M016.22.5|Technology Adoption
P|M016.22.6|Consumer Trend Diffusion
P|M016.22.7|Language and Translation Effects
P|M016.22.8|Voluntary Association Decisions
P|M016.22.9|Social Influence Events
P|M016.22.10|Society Simulation Tests
P|M016.23|Institutional Neutrality and Citizen Choice
P|M016.23.1|Institutional Neutrality Contracts
P|M016.23.2|No Forced Membership Rule
P|M016.23.3|No Forced Belief Rule
P|M016.23.4|No Forced Donation Rule
P|M016.23.5|Citizen Consent and Refusal
P|M016.23.6|Competing Commitments and Time Availability
P|M016.23.7|Employment and Institutional Participation Conflicts
P|M016.23.8|Evidence-Based Participation Decisions
P|M016.23.9|Neutrality Audit
P|M016.23.10|Neutrality Tests
P|M017|Data Export and Training-Asset Foundation
P|M017.1|JSON Export
P|M017.2|JSONL Export
P|M017.3|CSV Export
P|M017.4|YAML Export
P|M017.5|Markdown Export
P|M017.6|Dataset Metadata
P|M017.7|Dataset Versioning
P|M017.8|Dataset Provenance
P|M017.9|Data Masking
P|M017.10|Training Eligibility
P|M017.11|Retention Policies
P|M017.12|Export Tests
P|M017.13|Training Resource Contracts
P|M017.14|AI-Readiness Metadata
P|M017.15|Dataset Manifest
P|M017.16|Data Classification
P|M017.17|Consent and Purpose Constraints
P|M017.18|Label and Annotation Model
P|M017.19|Dataset Quality Metrics
P|M017.20|Dataset Splitting
P|M017.21|Dataset Lineage
P|M017.22|Dataset Integrity Hashes
P|M017.23|Training Dataset Registry
P|M017.24|Dataset Approval Workflow
P|M017.25|Cloud Training-Asset Storage Adapters
P|M017.25.1|Azure Blob Training-Asset Adapter
P|M017.25.2|Azure Archive Dataset Adapter
P|M017.25.3|Dataset Storage Provider Contracts
P|M017.25.4|Storage Quota Enforcement
P|M017.25.5|Cross-Provider Export Compatibility
P|M017.25.6|Training-Asset Export Tests
P|M017.26|Training-Asset Stabilization
P|M017.27|Longitudinal and Behavioural Dataset Generation
P|M017.27.1|Citizen Timeline Dataset
P|M017.27.2|Household Timeline Dataset
P|M017.27.3|Education Timeline Dataset
P|M017.27.4|Employment Timeline Dataset
P|M017.27.5|Business Timeline Dataset
P|M017.27.6|Financial Timeline Dataset
P|M017.27.7|Healthcare Timeline Dataset
P|M017.27.8|Supply-Chain Timeline Dataset
P|M017.27.9|Government and Policy Timeline Dataset
P|M017.27.10|Institutional Participation Timeline Dataset
P|M017.27.11|Cross-Lifecycle Causal Link Metadata
P|M017.27.12|Longitudinal Dataset Quality Tests
P|M018|PostgreSQL and Supabase Persistence
P|M018.1|PostgreSQL Architecture
P|M018.2|Database Schema Foundation
P|M018.3|Migration Framework
P|M018.4|SQL Repository Contracts
P|M018.5|SQL Event Repository
P|M018.6|SQL Registry Repositories
P|M018.7|Transaction Management
P|M018.8|Concurrency Controls
P|M018.9|Supabase Project Configuration
P|M018.10|Supabase Database Integration
P|M018.11|Supabase Storage Integration
P|M018.12|Backup and Recovery
P|M018.13|Database Security
P|M018.14|Persistence Integration Tests
P|M018.15|Persistence Stabilization
P|M018.16|Cloud PostgreSQL Provider Adapters
P|M018.16.1|Provider-Neutral Connection Contracts
P|M018.16.2|Azure PostgreSQL Configuration
P|M018.16.3|Supabase PostgreSQL Configuration
P|M018.16.4|Migration Compatibility
P|M018.16.5|Transaction Compatibility
P|M018.16.6|Backup Compatibility
P|M018.16.7|Cross-Provider Persistence Tests
P|M019|Platform Infrastructure and Deployment
P|M019.1|Infrastructure Contracts
P|M019.1.1|Environment Configuration
P|M019.1.2|Domain Configuration Contracts
P|M019.1.3|Secrets Configuration
P|M019.1.4|Storage Configuration
P|M019.1.5|Mail Provider Configuration
P|M019.1.6|Monitoring Configuration
P|M019.2|Domain and DNS Infrastructure
P|M019.2.1|Namecheap Domain Verification
P|M019.2.2|nexadata.live DNS Configuration
P|M019.2.3|API Subdomain Configuration
P|M019.2.4|Dashboard Subdomain Configuration
P|M019.2.5|Mail Subdomain Configuration
P|M019.2.6|SSL/TLS Configuration
P|M019.2.7|Domain Health Verification
P|M019.3|Mail Infrastructure
P|M019.3.1|Zoho Mail Workspace Configuration
P|M019.3.2|MX Records
P|M019.3.3|SPF Records
P|M019.3.4|DKIM Records
P|M019.3.5|DMARC Records
P|M019.3.6|Operational Mailboxes
P|M019.3.7|Mail Delivery Verification
P|M019.4|Deployment Infrastructure
P|M019.4.1|Application Hosting
P|M019.4.2|API Deployment
P|M019.4.3|Environment Separation
P|M019.4.4|Health Endpoints
P|M019.4.5|Logging
P|M019.4.6|Monitoring
P|M019.4.7|Alerting
P|M019.4.8|Deployment Tests
P|M019.5|Azure Development and Simulation Infrastructure
P|M019.5.1|Azure Student Subscription Boundaries
P|M019.5.2|Azure Resource Group Structure
P|M019.5.3|Azure Key Vault Configuration
P|M019.5.4|Azure Container Registry
P|M019.5.5|Azure Container Apps
P|M019.5.6|Azure Functions
P|M019.5.7|Azure Service Bus
P|M019.5.8|Azure Event Grid
P|M019.5.9|Azure PostgreSQL Adapter Deployment
P|M019.5.10|Azure Blob Storage
P|M019.5.11|Azure Archive Storage
P|M019.5.12|Azure AI Search Pilot
P|M019.5.13|Azure Machine Learning Workspace
P|M019.5.14|Azure Document Intelligence Pilot
P|M019.5.15|Azure Language Pilot
P|M019.5.16|Azure Content Safety Pilot
P|M019.5.17|Azure Monitor
P|M019.5.18|Azure Cost Management
P|M019.5.19|Budget and Quota Alerts
P|M019.5.20|Free-Tier Quota Verification
P|M019.5.21|Azure Infrastructure Tests
P|M019.6|Cloud Credit and Free-Tier Governance
P|M019.6.1|Cloud Credit Registry
P|M019.6.2|Credit Provider Contracts
P|M019.6.3|Credit Award Records
P|M019.6.4|Credit Expiry Tracking
P|M019.6.5|Service Eligibility Mapping
P|M019.6.6|Per-System Credit Allocation
P|M019.6.7|Monthly Usage Limits
P|M019.6.8|Token and Inference Budgets
P|M019.6.9|GPU-Hour Limits
P|M019.6.10|Storage Quota Limits
P|M019.6.11|Budget Alert Policies
P|M019.6.12|Automatic Shutdown Policies
P|M019.6.13|Free-Tier Boundary Monitoring
P|M019.6.14|Paid-Fallback Estimates
P|M019.6.15|Credit Usage Dashboard
P|M019.6.16|Credit Governance Audit
P|M019.6.17|Cloud Credit Governance Tests
P|M020|NPP Integration Readiness
P|M020.1|Public API Catalogue
P|M020.2|Client Authentication Contracts
P|M020.3|Registry Consumption Contracts
P|M020.4|Event Submission Contracts
P|M020.5|Data Query Contracts
P|M020.6|Dashboard Data Endpoints
P|M020.7|Mail Service Endpoints
P|M020.8|Integration Sandbox
P|M020.9|Client SDK Foundation
P|M020.10|Integration Documentation
P|M020.11|Integration Tests
P|M020.12|Integration-Ready Release
P|M020.13|Nexa-Bridge Integration Foundation
P|M020.13.1|Ecosystem Application Registration
P|M020.13.2|Application Capability Discovery
P|M020.13.3|Service Capability Contracts
P|M020.13.4|Cross-System Request Envelope
P|M020.13.5|Cross-System Response Envelope
P|M020.13.6|Cross-System Correlation
P|M020.13.7|Cross-System Idempotency
P|M020.13.8|API Versioning
P|M020.13.9|Application Authentication
P|M020.13.10|Scope and Permission Contracts
P|M020.13.11|Safe API Routing
P|M020.13.12|Command Routing
P|M020.13.13|Event Routing
P|M020.13.14|Service Bus Command Adapter
P|M020.13.15|Event Grid Publication Adapter
P|M020.13.16|Azure API Management Adapter
P|M020.13.17|Provider Gateway Integration
P|M020.13.18|Integration Error Contracts
P|M020.13.19|Integration Audit
P|M020.13.20|Integration Sandbox
P|M020.13.21|Client SDK Foundation
P|M020.13.22|Nexa-Bridge Integration Tests
P|M020.13.23|Nexa-Bridge Stabilization
P|M020.14|Client AI-Readiness Contracts
P|M020.14.1|AI Resource Capability Contract
P|M020.14.2|Training Resource Submission Contract
P|M020.14.3|Source-System Provenance Contract
P|M020.14.4|Client Data Classification Contract
P|M020.14.5|Client Masking Declaration
P|M020.14.6|Client Consent Declaration
P|M020.14.7|Client Purpose Restriction Contract
P|M020.14.8|Client Dataset Manifest
P|M020.14.9|Client Resource Schema Discovery
P|M020.14.10|Client Training-Resource Validation
P|M020.14.11|Client AI-Readiness Tests
P|M020.15|Ecosystem Application Integration Readiness
P|M020.15.1|iNexaMarket Application Registration
P|M020.15.2|CineWatch Application Registration
P|M020.15.3|Business Chamber Portal Registration
P|M020.15.4|Supplier Platform Registration
P|M020.15.5|Manufacturer Platform Registration
P|M020.15.6|Logistics Platform Registration
P|M020.15.7|Warehouse Platform Registration
P|M020.15.8|Application Identity Assignment
P|M020.15.9|Application Scope Assignment
P|M020.15.10|Callback and Webhook Registration
P|M020.15.11|Event Subscription Registration
P|M020.15.12|Schema-Version Registration
P|M020.15.13|Runtime-Mode Enforcement
P|M020.15.14|Simulation-Only Data Declaration
P|M020.15.15|Ecosystem Application Integration Tests
P|M020.16|Ecosystem Runtime Coordination
P|M020.16.1|Runtime Context API
P|M020.16.2|Simulation Status Discovery
P|M020.16.3|Production Status Discovery
P|M020.16.4|Execution Authority Exchange
P|M020.16.5|Runtime Capability Discovery
P|M020.16.6|Cross-System Runtime Validation
P|M020.16.7|Runtime Coordination Tests
P|M021|Operational Readiness
P|M021.1|Security Review
P|M021.2|Performance Testing
P|M021.3|Load Testing
P|M021.4|Failure Recovery Testing
P|M021.5|Backup Restoration Testing
P|M021.6|Audit Verification
P|M021.7|Monitoring Verification
P|M021.8|Operational Documentation
P|M021.9|Release Checklist
P|M021.10|Production Readiness Review
P|M022|NPP Alpha Release
P|M022.1|Release Candidate
P|M022.2|Full Test Suite
P|M022.3|Defect Stabilization
P|M022.4|Release Documentation
P|M022.5|Version Tag
P|M022.6|Production Deployment
P|M022.7|Production Verification
P|M022.8|NPP Alpha Released
P|M023|Education, Skills and Knowledge Platform
P|M023.1|Education Institution Registry
P|M023.2|School and Campus Registry
P|M023.3|Programme and Course Registry
P|M023.4|Student Registry
P|M023.5|Admission Lifecycle
P|M023.6|Attendance and Participation
P|M023.7|Assessment and Examination
P|M023.8|Qualification and Certificate Registry
P|M023.9|Skill and Competency Registry
P|M023.10|Apprenticeship and Vocational Training
P|M023.11|Education Finance and Sponsorship
P|M023.12|Education Events
P|M023.13|Education APIs
P|M023.14|Education Audit
P|M023.15|Education Tests
P|M024|Healthcare and Human Development Platform
P|M024.1|Healthcare Provider Registry
P|M024.2|Hospital and Clinic Registry
P|M024.3|Healthcare Worker Registry
P|M024.4|Patient Encounter Lifecycle
P|M024.5|Maternal and Child Health
P|M024.6|Immunisation Registry
P|M024.7|Diagnosis and Treatment Records
P|M024.8|Medicine and Pharmacy Foundation
P|M024.9|Health Insurance Integration
P|M024.10|Public Health Events
P|M024.11|Healthcare APIs
P|M024.12|Healthcare Audit
P|M024.13|Healthcare Tests
P|M025|Domestic Economy, Commerce and Supply Chains
P|M025.1|Product and Service Catalogue
P|M025.2|Retail Shop and Market Operations
P|M025.3|Customer Shopping Journey
P|M025.4|Basket and Shelf Selection Events
P|M025.5|Checkout and Payment Handoff
P|M025.6|Inventory and Warehousing
P|M025.7|Procurement and Supplier Relationships
P|M025.8|Transport and Logistics
P|M025.9|Agriculture and Food Supply Chains
P|M025.10|Manufacturing and Processing
P|M025.11|Wholesale and Distribution
P|M025.12|Domestic Trade
P|M025.13|Competition and Market Structure
P|M025.14|Economic Statistics
P|M025.15|Commerce and Supply-Chain Events
P|M025.16|Commerce APIs
P|M025.17|Commerce Tests
P|M026|Government, Constitution and Policy Platform
P|M026.1|Government Institution Registry
P|M026.2|Ministry and Agency Registry
P|M026.3|Civil Service Registry
P|M026.4|Constitutional Rule Engine
P|M026.5|Legal Eligibility and Age Rules
P|M026.6|Treasury and Public Accounts
P|M026.7|Revenue Authority and Taxation
P|M026.8|National Statistics Bureau
P|M026.9|Public Budget Lifecycle
P|M026.10|Public Service Programme Registry
P|M026.11|Policy Proposal and Scenario Model
P|M026.12|Policy Activation and Effective Dates
P|M026.13|Policy Impact Propagation
P|M026.14|Government Events
P|M026.15|Government APIs
P|M026.16|Government Audit
P|M026.17|Government Tests
P|M026.18|Legislative Platform
P|M026.18.1|Bill Registry
P|M026.18.2|Committee Workflow
P|M026.18.3|Parliamentary Session Model
P|M026.18.4|Voting and Passage Rules
P|M026.18.5|Law Assent and Publication
P|M026.18.6|Law Commencement
P|M026.18.7|Law Amendment and Repeal
P|M026.18.8|Policy Transition Simulation
P|M026.18.9|Legislative Events
P|M026.18.10|Legislative Tests
P|M026.19|Election and Government-Priority Simulation
P|M026.19.1|Election Eligibility Rules
P|M026.19.2|Electoral Administration Foundation
P|M026.19.3|Government Priority Profiles
P|M026.19.4|Policy Transition Scenarios
P|M026.19.5|Public Spending Priority Changes
P|M026.19.6|Election Events
P|M026.19.7|Election Simulation Tests
P|M027|Faith and Religious Institution Platform
P|M027.1|Institutional Neutrality Foundation
P|M027.1.1|Religious Freedom and Voluntary Participation
P|M027.1.2|Citizen Belief Privacy
P|M027.1.3|No Forced Conversion
P|M027.1.4|No Forced Attendance
P|M027.1.5|No Forced Donation
P|M027.1.6|Equal Institutional Treatment
P|M027.1.7|Religious Neutrality Audit
P|M027.1.8|Religious Neutrality Tests
P|M027.2|Faith and Belief Registry
P|M027.2.1|Faith Tradition Contracts
P|M027.2.2|Belief Profile Metadata
P|M027.2.3|Doctrine and Teaching Reference Assets
P|M027.2.4|Sacred Text Reference Metadata
P|M027.2.5|Practice and Observance Metadata
P|M027.2.6|Faith Tradition Versioning
P|M027.2.7|Faith Registry Tests
P|M027.3|Initial Faith Tradition Profiles
P|M027.3.1|Catholic Tradition Profile
P|M027.3.2|Anglican Tradition Profile
P|M027.3.3|Islamic Tradition Profile
P|M027.3.4|The Church of Jesus Christ of Latter-day Saints Tradition Profile
P|M027.3.5|Tradition-Specific Governance Validation
P|M027.3.6|Initial Tradition Profile Tests
P|M027.4|Religious Organisation Registry
P|M027.4.1|Organisation Contracts
P|M027.4.2|Headquarters and Jurisdiction Model
P|M027.4.3|Local Congregation Registry
P|M027.4.4|Religious Office and Authority Registry
P|M027.4.5|Volunteer and Missionary Assignment Registry
P|M027.4.6|Organisation Lifecycle
P|M027.4.7|Organisation Events
P|M027.4.8|Organisation APIs
P|M027.4.9|Organisation Tests
P|M027.5|Religious Membership and Participation
P|M027.5.1|Membership Contracts
P|M027.5.2|Citizen Interest and Enquiry
P|M027.5.3|Teaching and Instruction Sessions
P|M027.5.4|Citizen Understanding and Language Effects
P|M027.5.5|Citizen Acceptance or Refusal
P|M027.5.6|Membership Admission Requirements
P|M027.5.7|Baptism or Initiation Authority Validation
P|M027.5.8|Membership Confirmation and Recording
P|M027.5.9|Attendance and Participation
P|M027.5.10|Inactivity without Automatic Removal
P|M027.5.11|Membership Transfer and Migration
P|M027.5.12|Membership Lifecycle Events
P|M027.5.13|Membership Tests
P|M027.6|Missionary and Outreach Operations
P|M027.6.1|Missionary Department Registry
P|M027.6.2|Mission and Area Assignment
P|M027.6.3|International Missionary Visa Dependency
P|M027.6.4|Missionary Couple Assignment
P|M027.6.5|Local Missionary Calling
P|M027.6.6|Door-to-Door Outreach
P|M027.6.7|Market and Community Outreach
P|M027.6.8|Teaching Appointment Scheduling
P|M027.6.9|Local Language Translation Support
P|M027.6.10|Missionary Material Inventory
P|M027.6.11|Outreach Events
P|M027.6.12|Outreach Tests
P|M027.7|Latter-day Saint Organisational Lifecycle Profile
P|M027.7.1|Zero-Member Country Initial State
P|M027.7.2|Migrant Member and Family Arrival
P|M027.7.3|Home-Based Group Formation
P|M027.7.4|Priesthood Authority Validation
P|M027.7.5|Baptism and Confirmation Authority Rules
P|M027.7.6|Priesthood Ordination Lifecycle
P|M027.7.7|Group Leader Assignment
P|M027.7.8|Branch Formation Request
P|M027.7.9|Branch Organisation
P|M027.7.10|Ward Formation
P|M027.7.11|Stake Formation
P|M027.7.12|Mission Formation
P|M027.7.13|Temple District Formation
P|M027.7.14|Temple Planning and Construction Lifecycle
P|M027.7.15|Latter-day Saint Lifecycle Tests
P|M027.8|Religious Programmes and Internal Organisations
P|M027.8.1|Children and Primary Programme
P|M027.8.2|Youth Programme
P|M027.8.3|Young Single Adult Programme
P|M027.8.4|Women and Relief Society Organisation
P|M027.8.5|Men and Elders Quorum Organisation
P|M027.8.6|Religious Education Programme
P|M027.8.7|Leadership Training
P|M027.8.8|Programme Participation Events
P|M027.8.9|Programme Tests
P|M027.9|Religious Finance and Property
P|M027.9.1|Religious Account Ownership
P|M027.9.2|Voluntary Tithing and Donation Decisions
P|M027.9.3|Fast Offering and Charitable Fund Model
P|M027.9.4|Headquarters Funding Transfers
P|M027.9.5|Local Budget Allocation
P|M027.9.6|Land Search and Purchase
P|M027.9.7|Building Approval and Construction
P|M027.9.8|Meetinghouse Operations
P|M027.9.9|Temple Property Operations
P|M027.9.10|Religious Finance Audit
P|M027.9.11|Religious Finance Tests
P|M027.10|Faith, Employment and Social Effects
P|M027.10.1|Work-Schedule and Worship Conflict
P|M027.10.2|Religious Accommodation by Employers
P|M027.10.3|Citizen Employment Preference Effects
P|M027.10.4|Family-Level Mixed Participation
P|M027.10.5|Community Acceptance and Resistance
P|M027.10.6|Institutional Growth without System Bias
P|M027.10.7|Social-Effect Events
P|M027.10.8|Social-Effect Tests
P|M027.11|Faith Knowledge and Training Assets
P|M027.11.1|Source Provenance Requirements
P|M027.11.2|Tradition-Specific Terminology
P|M027.11.3|Teaching Material Metadata
P|M027.11.4|Translation Dataset Governance
P|M027.11.5|Religious Knowledge Safety and Neutrality
P|M027.11.6|NexVox Institutional-Learning Export
P|M027.11.7|No Persuasion Training Constraint
P|M027.11.8|Faith Dataset Quality Tests
P|M028|International Relations, Migration and Trade Platform
P|M028.1|Multi-Country Registry
P|M028.2|Nationality and Citizenship Relationships
P|M028.3|Passport Registry
P|M028.4|Visa Registry
P|M028.5|Visa Application Lifecycle
P|M028.6|Immigration and Border Entry
P|M028.7|Residence and Migration Lifecycle
P|M028.8|Customs Foundation
P|M028.9|Port and Airport Registry
P|M028.10|International Cargo and Logistics
P|M028.11|International Trade
P|M028.12|Trade Agreements
P|M028.13|Exchange Rates
P|M028.14|Foreign Investment
P|M028.15|Tourism
P|M028.16|Diplomatic Relationship Model
P|M028.17|International Events
P|M028.18|International APIs
P|M028.19|International Audit
P|M028.20|International Tests
P|M029|NexVox Observational Intelligence Platform
P|M029.1|Observational Intelligence Contracts
P|M029.2|Read-Only Event and Read-Model Access
P|M029.3|Pattern Detection
P|M029.4|Trend Detection
P|M029.5|Risk Detection
P|M029.6|Market-Gap Detection
P|M029.7|Supply-Chain Gap Detection
P|M029.8|Citizen Opportunity Analysis
P|M029.9|Business Opportunity Analysis
P|M029.10|Investment Opportunity Analysis
P|M029.11|Policy Impact Analysis
P|M029.12|Scenario Comparison
P|M029.13|Evidence and Provenance Binding
P|M029.14|Confidence Scoring
P|M029.15|Explainable Recommendations
P|M029.16|Recommendation Review and Feedback
P|M029.17|No Autonomous Execution Boundary
P|M029.18|No Citizen Impersonation Boundary
P|M029.19|No Forced Institutional Participation Boundary
P|M029.20|NexVox Audit
P|M029.21|NexVox APIs
P|M029.22|NexVox Tests
P|M030|Sovereign Simulation Integration and Stabilisation
P|M030.1|Cross-Lifecycle Integration
P|M030.2|Village Simulation Baseline
P|M030.3|Ward and District Scaling
P|M030.4|Province and National Scaling
P|M030.5|Multi-Country Scaling
P|M030.6|Deterministic Society Replay
P|M030.7|Causal Event-Graph Verification
P|M030.8|Institutional Neutrality Verification
P|M030.9|Simulation-to-Production Provider Replacement
P|M030.10|Sovereign Simulation Load Testing
P|M030.11|Sovereign Simulation Release Candidate
P|M030.12|Sovereign Simulation Platform Stabilised
""".strip()


def _parent_number(number: str) -> str | None:
    return number.rsplit(".", 1)[0] if "." in number else None


def _parse_rows(outline: str) -> list[dict[str, object]]:
    raw_rows: list[tuple[str, str, str]] = []
    for line_number, raw_line in enumerate(outline.splitlines(), start=1):
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split("|", 2)
        if len(parts) != 3:
            raise ValueError(f"Invalid roadmap row at line {line_number}: {raw_line!r}")
        marker, number, title = (part.strip() for part in parts)
        if marker not in {"C", "P"}:
            raise ValueError(f"Unknown status marker {marker!r} at line {line_number}")
        if not number.startswith("M") or not title:
            raise ValueError(f"Invalid milestone at line {line_number}: {raw_line!r}")
        raw_rows.append((marker, number, title))

    title_by_number = {number: title for _, number, title in raw_rows}
    records: list[dict[str, object]] = []
    for sequence, (marker, number, title) in enumerate(raw_rows, start=1):
        parent_number = _parent_number(number)
        lineage = [title]
        ancestor = parent_number
        while ancestor is not None:
            if ancestor not in title_by_number:
                raise ValueError(f"Milestone {number} references missing parent {ancestor}")
            lineage.append(title_by_number[ancestor])
            ancestor = _parent_number(ancestor)
        semantic_path = " / ".join(reversed(lineage))
        record_hash = sha256(f"npp-roadmap::{semantic_path}".encode()).hexdigest()[:20]
        records.append({
            "record_id": f"npp-rm-{record_hash}",
            "number": number,
            "title": title,
            "status": STATUS_COMPLETED if marker == "C" else STATUS_PLANNED,
            "sequence": sequence,
            "depth": number.count("."),
            "parent_number": parent_number,
            "semantic_path": semantic_path,
            "dependencies": (),
            "priority": "NORMAL",
            "started_date": None,
            "completed_date": None,
            "commit_hash": None,
            "passing_tests": None,
            "verification_state": "UNVERIFIED",
            "notes": (),
        })
    return records


def _validate(records: Iterable[Mapping[str, object]]) -> None:
    rows = list(records)
    numbers = [str(row["number"]) for row in rows]
    record_ids = [str(row["record_id"]) for row in rows]
    if not rows or numbers[0] != ROADMAP_START or numbers[-1] != ROADMAP_END:
        raise ValueError("Roadmap boundaries are invalid.")
    if len(numbers) != len(set(numbers)):
        raise ValueError("Duplicate milestone numbers detected.")
    if len(record_ids) != len(set(record_ids)):
        raise ValueError("Duplicate internal record IDs detected.")
    known = set(numbers)
    for expected_sequence, row in enumerate(rows, start=1):
        if row["sequence"] != expected_sequence:
            raise ValueError(f"Sequence mismatch for {row['number']}")
        if row["status"] not in ALLOWED_STATUSES:
            raise ValueError(f"Invalid status for {row['number']}")
        parent = row["parent_number"]
        if parent is not None and parent not in known:
            raise ValueError(f"Missing parent {parent} for {row['number']}")
    roots = [number for number in numbers if "." not in number]
    end_root = int(ROADMAP_END.split(".", 1)[0][1:])
    expected_roots = [f"M{value:03d}" for value in range(1, end_root + 1)]
    if roots != expected_roots:
        raise ValueError(
            f"Root milestones must be sequential from M001 to M{end_root:03d}."
        )


_MUTABLE_MILESTONES = _parse_rows(_ROADMAP_OUTLINE)
_validate(_MUTABLE_MILESTONES)

MILESTONES: Final[tuple[Mapping[str, object], ...]] = tuple(
    MappingProxyType(record) for record in _MUTABLE_MILESTONES
)
MILESTONE_INDEX: Final[Mapping[str, Mapping[str, object]]] = MappingProxyType(
    {str(record["number"]): record for record in MILESTONES}
)
RECORD_ID_INDEX: Final[Mapping[str, Mapping[str, object]]] = MappingProxyType(
    {str(record["record_id"]): record for record in MILESTONES}
)
ROOT_MILESTONES: Final[tuple[Mapping[str, object], ...]] = tuple(
    record for record in MILESTONES if record["parent_number"] is None
)
TOTAL_MILESTONES: Final[int] = len(MILESTONES)
COMPLETED_MILESTONES: Final[int] = sum(
    1 for record in MILESTONES if record["status"] == STATUS_COMPLETED
)
PLANNED_MILESTONES: Final[int] = TOTAL_MILESTONES - COMPLETED_MILESTONES


def get_milestone(number: str) -> Mapping[str, object]:
    try:
        return MILESTONE_INDEX[number]
    except KeyError as exc:
        raise KeyError(f"Unknown roadmap milestone: {number}") from exc


def get_children(number: str) -> tuple[Mapping[str, object], ...]:
    get_milestone(number)
    return tuple(record for record in MILESTONES if record["parent_number"] == number)


def get_descendants(number: str) -> tuple[Mapping[str, object], ...]:
    get_milestone(number)
    prefix = f"{number}."
    return tuple(record for record in MILESTONES if str(record["number"]).startswith(prefix))


def roadmap_summary() -> Mapping[str, object]:
    return MappingProxyType({
        "title": ROADMAP_TITLE,
        "version": ROADMAP_VERSION,
        "start": ROADMAP_START,
        "end": ROADMAP_END,
        "root_milestones": len(ROOT_MILESTONES),
        "total_milestones": TOTAL_MILESTONES,
        "completed_milestones": COMPLETED_MILESTONES,
        "planned_milestones": PLANNED_MILESTONES,
    })


__all__ = [
    "ALLOWED_STATUSES", "COMPLETED_MILESTONES", "MILESTONE_INDEX",
    "MILESTONES", "PLANNED_MILESTONES", "RECORD_ID_INDEX",
    "ROADMAP_END", "ROADMAP_START", "ROADMAP_TITLE", "ROADMAP_VERSION",
    "ROOT_MILESTONES", "STATUS_COMPLETED", "STATUS_PLANNED",
    "TOTAL_MILESTONES", "get_children", "get_descendants",
    "get_milestone", "roadmap_summary",
]
