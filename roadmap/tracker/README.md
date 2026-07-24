# NPP Roadmap Tracker Engine

The tracker is the operational engineering companion to the immutable NPP
architectural roadmap.

## Authority boundary

- `roadmap_data.py` and `ROADMAP.md` remain the architectural authority.
- Tracker extensions and tracker-only milestones exist only in tracker data.
- Architectural titles, numbers and completion percentages are loaded
  dynamically from the current architecture snapshot.
- The tracker has no architecture mutation API.
- `ROADMAP_TRACKER.md` is generated at repository root.

## Standard build

```bash
python roadmap_tracker.py
```

The command performs:

1. Validate architecture roadmap.
2. Generate `ROADMAP.md`.
3. Load the newly updated immutable architecture snapshot.
4. Recalculate tracker architecture progress.
5. Generate `ROADMAP_TRACKER.md`.
6. Validate both outputs are synchronized.

## Data

Operational tracker records are stored in:

```text
roadmap/tracker/data/tracker_records.json
```

The initial file is intentionally empty. Engineering records are added only
after their scope, ownership and evidence are approved.
