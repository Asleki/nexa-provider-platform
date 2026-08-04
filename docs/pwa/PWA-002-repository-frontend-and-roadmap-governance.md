# PWA-002 — Repository, Frontend and Roadmap Governance

## Document control

| Field | Value |
|---|---|
| Document ID | `PWA-002` |
| Parent foundation | `P001 — NexiLabs PWA Project Foundation` |
| Repository | `nexa-provider-platform` |
| Status | Normative foundation |

## Purpose

This document combines the repository placement, naming, frontend-boundary, and
roadmap-governance decisions that were previously split into several
administrative mini milestones.

These decisions are documentation foundations, not independent product
capabilities. Real engineering milestones must introduce executable frontend,
map, offline, deployment, or API behaviour.

## Canonical repository placement

The PWA remains in the existing monorepository:

```text
nexa-provider-platform/
```

The current application boundary is:

```text
frontend/
```

Normative PWA documents belong in:

```text
docs/pwa/
```

PWA roadmap governance remains at repository root:

```text
PWA_ROADMAP.md
pwa_roadmap.py
pwa_roadmap_data.py
pwa_roadmap_frontend.py
```

## Canonical brand assets

The existing NexiLabs brand assets remain authoritative at:

```text
frontend/public/brand/nexilabs/
├── icons/
├── logos/
├── metadata/
├── pwa/
├── social/
└── vectors/
```

Application milestones must consume these assets rather than create duplicate
canonical copies.

## Reserved frontend structure

Later executable milestones may create:

```text
frontend/
├── index.html
├── public/
├── src/
│   ├── app/
│   ├── branding/
│   ├── config/
│   ├── core/
│   ├── map/
│   ├── simulation/
│   ├── styles/
│   └── ui/
├── tests/
├── scripts/
└── dist/
```

This is a reserved semantic structure. A directory should be created only when
the active milestone introduces real code that owns that responsibility.

## Naming rules

- directories use lowercase kebab-case or established lowercase names;
- Python files use lowercase snake_case;
- JavaScript modules use lowercase kebab-case;
- test names describe observable behaviour;
- generated output is not edited by hand;
- map, layer, dataset, event, runtime, registry, and world-state identifiers
  must remain semantically distinct;
- generic unqualified `id` fields are discouraged at cross-system boundaries.

## Generated and authoritative files

`pwa_roadmap_data.py` is the canonical roadmap source.

`PWA_ROADMAP.md` is generated output.

The correct update flow is:

```bash
python pwa_roadmap_frontend.py
python pwa_roadmap.py verify
python pwa_roadmap_frontend.py --check
```

The main NPP roadmap generator is not used for PWA-only status changes.

## Roadmap design rule

A functional roadmap milestone must answer:

> What executable or observable product capability exists after this milestone
> that did not exist before?

Good milestone outcomes include:

- the application boots;
- branding renders;
- the manifest installs;
- the offline shell loads;
- the map displays;
- coordinates convert;
- terrain layers render;
- AWS deployment succeeds;
- an approved API query returns safe data.

Documentation-only outcomes must be consolidated into foundation documents and
must not dominate the engineering roadmap.

## Stable roadmap identity

Visible milestone numbers and stable record IDs serve different purposes.

- visible numbers communicate sequence;
- stable record IDs preserve identity;
- semantic titles must not be casually renamed after completion;
- completed milestones are immutable except for verified maintenance;
- roadmap restructuring must preserve completed evidence and explain any
  superseded planning records.

## Locked outcome

The repository has one PWA application boundary, one canonical brand location,
one PWA roadmap source, one generated roadmap view, and a practical rule that
future milestones must produce real application capability rather than merely
more documentation.
