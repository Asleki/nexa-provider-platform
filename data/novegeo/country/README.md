# NoveGeo Sovereign Country Source

P006.7.1 Bundle 13A introduces the stable sovereign-country reference used by later NNGLA and registry work.

The CSV in `source/` is governed migration-source evidence only. The PWA and operational services must never read this CSV as authoritative runtime state. Canonical operational persistence is reserved for the later PostgreSQL authority milestone, after Python validation and controlled migration.

The sovereign boundary is not copied into this folder. Bundle 13A references the already-qualified `boundary:novegeo:sovereign` geography authority and its active version.
