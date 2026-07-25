"""
Nexa Provider Platform (NPP)
File: roadmap_data.py

Authoritative structured roadmap data for the NPP engineering roadmap.
Visible milestone numbers are positional and may be renumbered after insertion.
Internal record IDs are derived from semantic title paths so ordinary number
changes do not break identity. M001-M006 are COMPLETED; M007 onward PLANNED.
"""
from __future__ import annotations
from hashlib import sha256
from types import MappingProxyType
from typing import Final, Iterable, Mapping

STATUS_COMPLETED: Final[str] = "COMPLETED"
STATUS_PLANNED: Final[str] = "PLANNED"
ALLOWED_STATUSES: Final[frozenset[str]] = frozenset({STATUS_COMPLETED, STATUS_PLANNED})
ROADMAP_VERSION: Final[str] = "1.0.0"
ROADMAP_TITLE: Final[str] = "Nexa Provider Platform — Final Scope Engineering Roadmap"
ROADMAP_START: Final[str] = "M001"
ROADMAP_END: Final[str] = "M022.8"

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
P|M008|Master Registry Foundation
C|M008.1|Registry Contracts
C|M008.2|Registry Identifier Model
C|M008.3|Base Registry
C|M008.4|Registry Repository Interface
C|M008.5|Memory Registry Repository
P|M008.6|Registry Factory
P|M008.7|Registry Catalogue
P|M008.8|Registry Lifecycle
P|M008.9|Registry Validation
P|M008.10|Registry Events
P|M008.11|Registry APIs
P|M008.12|Registry Audit Integration
P|M008.13|Registry Tests
P|M008.14|Registry Stabilization
P|M009|Data Catalogue and Communication Foundations
P|M009.1|Name Catalogue
P|M009.1.1|First-Name Catalogue
P|M009.1.2|Middle-Name Catalogue
P|M009.1.3|Surname Catalogue
P|M009.1.4|Name Metadata
P|M009.1.5|Name Repository
P|M009.1.6|Name Search
P|M009.1.7|Name Catalogue Tests
P|M009.2|Name Suggestion Engine
P|M009.2.1|Manual Name Entry
P|M009.2.2|Single-Name Suggestions
P|M009.2.3|Pair Suggestions
P|M009.2.4|Trio Suggestions
P|M009.2.5|Full-Name Suggestions
P|M009.2.6|Name Normalization
P|M009.2.7|Duplicate Controls
P|M009.2.8|Suggestion APIs
P|M009.2.9|Suggestion Tests
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
    if roots != [f"M{value:03d}" for value in range(1, 23)]:
        raise ValueError("Root milestones must be sequential from M001 to M022.")


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
