# PWA-001 — Scope and Product Boundary

## Document control

| Field | Value |
|---|---|
| Document ID | `PWA-001` |
| Roadmap foundation | `P001 — NexiLabs PWA Project Foundation` |
| Product | NexiLabs NoveGeo PWA |
| Runtime target | AWS |
| Repository | `nexa-provider-platform` |
| Status | Normative foundation |

## Purpose

The NexiLabs NoveGeo PWA is an installable AWS-hosted browser application whose
first operational purpose is to display and interact with the simulated country
of NoveGeo.

The initial product is deliberately narrow. It establishes the world map,
coordinates, terrain, water, climate, vegetation, navigation, simulation time,
and controlled dynamic-world presentation before National, School, Business,
Health, Monetary, or other registries are exposed through the frontend.

## Product definition

The PWA is:

- a browser presentation and interaction client;
- a NoveGeo map and world-state interface;
- a future consumer of secured NPP APIs;
- an installable and offline-capable web application;
- an AWS-hosted product.

The PWA is not:

- the Nexa Provider Platform itself;
- a PostgreSQL administration client;
- a registry authority;
- a financial processor;
- a National ID issuer;
- a substitute for NexaPOS Alpha;
- a direct browser-to-database interface.

## Authority boundary

The authoritative direction is:

```text
NexiLabs PWA
    ↓ HTTPS
Secured, versioned NPP/AWS API
    ↓
NPP services and read models
    ↓
PostgreSQL
```

Browser JavaScript must never hold PostgreSQL credentials or connect directly to
an RDS/PostgreSQL endpoint.

## Initial NoveGeo scope

The first application release may implement:

- a governed national/world boundary;
- latitude and longitude;
- equator reference;
- projection and viewport rules;
- terrain and elevation;
- mountains, valleys, plains and plateaus;
- rivers, lakes and drainage;
- climate and rainfall presentation;
- windward and leeward effects;
- vegetation and arid regions;
- map navigation and layer controls;
- a one-to-one simulation clock presentation;
- versioned dynamic world-state snapshots.

## Runtime separation

`development`, `testing`, `simulation`, `staging`, and `production` must remain
explicit and distinguishable.

Simulation content must never be silently presented as production truth.
Production data must never be copied into simulation merely for convenience.

## Future registry relationship

Later systems may expose approved map references for citizens, households,
businesses, schools, hospitals, banks, farms, roads, markets, and infrastructure.

Those systems remain authoritative for their own identities and lifecycle. The
PWA displays stable references and safe summaries; it does not embed or replace
complete registry records.

## NexaPOS Alpha relationship

NexaPOS Alpha remains an operational event-producing system. In a later
integration, NPP may expose approved geographic read models derived from
NexaPOS events. The PWA may display those summaries but does not own or mutate
NexaPOS operational records.

## Privacy and security

The PWA must:

- receive only fields authorized for the active user and runtime;
- avoid secrets in browser-delivered files;
- treat cached data as a local copy, never the system of record;
- support stricter response filtering without replacing stable identities;
- avoid reconstructing hidden personal information;
- separate public, restricted, and administrative data.

## Cross-roadmap rule

PWA completion may provide evidence toward a main NPP roadmap record, but it
never automatically completes one. Each roadmap is updated and verified
separately.

## Locked outcome

The NexiLabs NoveGeo PWA is an AWS-hosted, installable map and world-state
client. It consumes future NPP capabilities only through secured APIs, never
connects directly to PostgreSQL, never replaces authoritative registries, and
can expand through stable references without changing its foundational identity.
