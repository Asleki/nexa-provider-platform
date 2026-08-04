# PWA-001 — NexiLabs PWA Scope and Product Boundary

## 1. Document control

| Field | Value |
|---|---|
| Document ID | `PWA-001` |
| Roadmap milestone | `P001.1 — PWA Scope and Product Boundary` |
| Product | NexiLabs NoveGeo PWA |
| Status | Normative foundation |
| Runtime hosting target | AWS |
| Initial product scope | NoveGeo map and world visualisation |
| Authoritative backend | Nexa Provider Platform (NPP) |

## 2. Purpose

This document establishes the permanent scope, authority, integration, safety,
and extension boundaries of the NexiLabs NoveGeo Progressive Web Application
before frontend application code is introduced.

The boundary prevents the PWA from becoming an accidental registry authority,
database administration client, payment processor, identity issuer, or source
of ungoverned simulation facts.

## 3. Product definition

The **NexiLabs NoveGeo PWA** is an installable browser application hosted on AWS.
Its first operational purpose is to present, inspect, and interact with the
simulated geography and evolving world state of NoveGeo.

The PWA is a client of NPP. It does not replace NPP, PostgreSQL repositories,
registry services, event infrastructure, audit infrastructure, or simulation
engines.

## 4. Initial product scope

The initial product is limited to the NoveGeo map and its supporting visual
foundation. The approved initial scope includes future implementation of:

- a governed NoveGeo world boundary;
- latitude and longitude presentation;
- an equator reference;
- map projection and coordinate conversion;
- terrain, elevation, mountains, valleys, plateaus, plains, and slopes;
- rivers, lakes, drainage, climate, rainfall, temperature, and vegetation;
- map pan, zoom, selection, layer controls, legend, and scale;
- simulation date, clock, world-state version, and dynamic layer presentation;
- an installable and offline-capable application shell;
- secure, versioned API consumption as NPP capabilities become available.

The initial PWA may use versioned static or generated datasets while the
relevant NPP registries and services do not yet exist. Such datasets must retain
source, version, runtime mode, and provenance information and must not be
presented as authoritative registry records.

## 5. Runtime hosting boundary

AWS is the runtime hosting target for the PWA. GitHub remains the source-control,
review, history, and roadmap-publication platform.

AWS hosting does not grant the frontend authority over NPP or PostgreSQL. The
specific AWS services, deployment topology, DNS, certificates, cache policy,
monitoring, and rollback strategy are deferred to the AWS hosting milestone.

No AWS access key, secret key, session token, database password, or private
service credential may be embedded in frontend source, static assets, browser
storage, generated JavaScript, or public runtime configuration.

## 6. Relationship to Nexa Provider Platform

NPP is the authoritative provider platform. The PWA is a presentation and
interaction client.

The required direction is:

```text
NexiLabs PWA
    ↓ HTTPS
versioned and secured API boundary
    ↓
NPP application and query services
    ↓
NPP repositories and authoritative stores
```

The PWA may display approved authoritative records, derived read models,
aggregates, and simulation state returned by NPP. It must not bypass NPP domain
services to create, mutate, approve, promote, or delete authoritative records.

Every authoritative record continues to have one owning domain. A visual map
feature may reference that record, but the visual feature does not become its
owner.

## 7. PostgreSQL boundary

A browser client must never connect directly to PostgreSQL.

The prohibited direction is:

```text
browser JavaScript → PostgreSQL / Amazon RDS
```

The approved direction is:

```text
browser PWA → HTTPS API → NPP service → PostgreSQL repository
```

Public frontend configuration must reject or exclude:

- PostgreSQL connection strings;
- Amazon RDS hostnames;
- port `5432` connection material;
- database usernames or passwords;
- administrative SQL capability;
- unrestricted table or schema access.

The PWA consumes purpose-limited responses, not raw database authority.

## 8. Relationship to NexaPOS Alpha

NexaPOS Alpha remains an independent operational application. P001.1 does not
integrate NexaPOS Alpha and does not change its contracts, event flows, offline
behaviour, or repositories.

Future approved integration may allow NPP to receive or derive geographic
summaries from NexaPOS events and expose safe read models to the PWA. Such future
operations may carry explicit identifiers including `event_id`, `estate_id`,
`business_unit_id`, `device_id`, `location_id`, and `runtime_mode`.

The PWA must not directly read NexaPOS local storage, impersonate NexaPOS users,
or mutate NexaPOS operational state.

## 9. Simulation and production separation

Simulation and production are distinct execution contexts. The runtime mode
must be explicit in configuration and in data responses where the distinction
matters.

The PWA must not:

- infer runtime mode from a hostname, colour, user assumption, or data value;
- merge simulation and production records into one unlabelled result;
- promote simulation data into production;
- present generated simulation facts as production facts;
- allow an offline cache entry from one runtime to satisfy another runtime.

Future runtime identities may include `development`, `testing`, `simulation`,
`staging`, and `production`, subject to the authoritative NPP runtime contract.

## 10. Data ownership

The PWA owns presentation state only, including permitted view state, selected
layers, viewport position, non-sensitive display preferences, and cache
metadata.

It does not own:

- citizen identity;
- birth or civil registration;
- business identity or lifecycle;
- school, student, or qualification records;
- healthcare or clinical records;
- bank accounts, balances, cards, payments, or monetary policy;
- authoritative geography or infrastructure records;
- Name Catalogue authority;
- NPP events, approvals, or audit records.

Cached data is a local copy for presentation and offline continuity. It is not
the system of record.

## 11. Identifier and reference boundaries

Later PWA operations may carry multiple identifiers at the same time. Each must
remain semantically named and must not be substituted by an ambiguous generic
`id` field.

Reserved identifier concepts include:

- `map_feature_id`;
- `map_layer_id`;
- `world_state_version`;
- `dataset_id`;
- `location_id`;
- `registry_record_id`;
- `event_id`;
- `simulation_scenario_id`;
- `runtime_mode`;
- `request_id`;
- `correlation_id`;
- future domain identifiers such as `citizen_id`, `business_id`,
  `institution_id`, and `estate_id`.

Reserving these names does not implement their contracts or allocate identities.

## 12. Future registry extension model

Later registries may expose safe map references without embedding their complete
records in map data.

Examples include:

- a Citizen Registry exposing an authorized location reference or aggregate;
- a Business Registry exposing an approved business marker and category;
- an Education Registry exposing school locations and catchment summaries;
- a Healthcare Registry exposing facility locations and service coverage;
- a Banking Registry exposing branches, ATMs, or aggregated service coverage;
- a Geography Registry exposing governed locations and hierarchies.

The owning registry retains legal identity, lifecycle, policy, authorization,
and audit responsibility. The PWA receives only the fields permitted for the
current user, purpose, runtime, and screen.

## 13. Cross-roadmap completion rule

PWA work may provide implementation evidence for an NPP roadmap record, but it
must never automatically mark an NPP record complete.

Completion requires separate inspection of the NPP acceptance criteria and a
separate deliberate update to the NPP canonical roadmap.

Likewise, an NPP milestone does not automatically complete a PWA milestone
unless the PWA acceptance criteria, tests, documentation, and delivery evidence
have passed.

## 14. Security and privacy boundary

The PWA follows least privilege and data minimisation.

It must:

- use HTTPS for network access;
- request only data needed by the current capability;
- render only fields returned by the authorized API response;
- avoid reconstructing hidden personal information;
- keep credentials and secrets outside public frontend code;
- preserve runtime and tenant or scope boundaries;
- support stricter privacy policies without replacing stable identities;
- avoid placing sensitive personal, financial, healthcare, or identity data in
  public static map datasets.

Stable identifiers may remain unchanged while API visibility becomes more
restrictive, masked, aggregated, or role-dependent.

## 15. Offline and cached-state boundary

Offline capability means the approved application shell and permitted cached
presentation data can remain available during connectivity loss.

Offline capability does not grant authority to:

- create or approve registry records;
- execute financial transactions;
- issue identities;
- bypass online-only authorization;
- merge data across runtime modes;
- treat stale cached state as current authoritative state.

Later milestones must define cache ownership, versioning, expiry, invalidation,
and runtime isolation.

## 16. Current exclusions

P001.1 does not implement or authorize:

- frontend application directories or application bootstrap;
- HTML, CSS, JavaScript, service workers, or map rendering;
- AWS infrastructure or deployment;
- direct PostgreSQL access;
- public or private API endpoints;
- authentication or authorization flows;
- citizen, birth, household, business, school, healthcare, banking, government,
  or other operational registry interfaces;
- payments, balances, settlement, currency issuance, or monetary decisions;
- autonomous simulation decisions or production actions;
- NexaPOS integration;
- Name Catalogue authoring from the browser;
- claims that NoveGeo is a real Earth jurisdiction.

## 17. Reserved capabilities

The product boundary reserves extension points for:

- versioned map and world-state datasets;
- secured NPP APIs;
- authentication and role-aware responses;
- Name Catalogue browsing and filtered search;
- governed geography and infrastructure layers;
- registry-owned map markers;
- simulation event and state presentation;
- privacy-filtered aggregates;
- NexaPOS-derived geographic read models;
- citizen, business, school, health, financial, and government visualisations
  after their authoritative systems exist.

Reservation is not implementation and does not imply readiness.

## 18. Deferred capabilities

Domain engines, registries, calculations, operational workflows, infrastructure,
and database adapters are implemented only by their owning later milestones.

Known deferred work includes frontend directory creation, technology selection,
AWS hosting implementation, application runtime configuration, map coordinates,
terrain, climate, interaction, dynamic simulation state, API integration,
PostgreSQL-backed screens, security qualification, and Alpha release.

## 19. Acceptance criteria

P001.1 is acceptable only when:

1. The product is explicitly defined as an AWS-hosted NexiLabs NoveGeo PWA.
2. The first scope is limited to NoveGeo map and world visualisation.
3. NPP is identified as the authoritative backend platform.
4. Direct browser-to-PostgreSQL access is explicitly prohibited.
5. HTTPS and a secured, versioned API boundary are required.
6. Simulation and production remain explicitly distinguishable.
7. The PWA is not treated as a registry authority or system of record.
8. NexaPOS Alpha remains separate and unmodified.
9. Future registries can link through stable, semantically named references.
10. Privacy may become stricter without replacing stable identities.
11. PWA completion does not automatically complete an NPP milestone.
12. Secrets and private credentials are prohibited from public frontend assets.
13. Current exclusions, reserved capabilities, and deferred capabilities are
    explicit.
14. Additive contract tests verify these durable decisions.

## 20. Guiding principle

> The NexiLabs PWA presents the simulated world; NPP and its owning domains
> remain authoritative for the facts, identities, rules, events, and decisions
> that the world contains.
