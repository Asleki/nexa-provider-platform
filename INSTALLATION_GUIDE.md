# ROADMAP_TRACKER_ENGINE Installation Guide

Copy the package contents into the repository root without replacing any
existing architecture file.

```text
nexa-provider-platform/
├── ROADMAP.md                         # existing; unchanged by this package
├── ROADMAP_TRACKER.md                 # generated at runtime
├── roadmap.py                         # existing; unchanged
├── roadmap_data.py                    # existing; unchanged
├── roadmap_frontend.py                # existing; unchanged
├── roadmap_tracker.py                 # new six-stage wrapper
│
├── roadmap/
│   ├── ...                            # existing roadmap modules, unchanged
│   └── tracker/
│       ├── __init__.py
│       ├── architecture.py
│       ├── models.py
│       ├── storage.py
│       ├── extensions.py
│       ├── commits.py
│       ├── files.py
│       ├── progress.py
│       ├── validation.py
│       ├── dashboard.py
│       ├── generator.py
│       ├── engine.py
│       ├── tracker_git.py
│       ├── tracker_reports.py
│       ├── tracker_*.py               # explicit-name compatibility modules
│       ├── README.md
│       └── data/
│           └── tracker_records.json
│
└── tests/
    ├── unit/roadmap/tracker/
    │   └── test_*.py
    └── integration/roadmap/
        └── test_tracker_pipeline.py
```

## First test

From the repository root:

```bash
PYTHONPATH=. python -m unittest discover -s tests/unit/roadmap/tracker -p "test_*.py" -v
PYTHONPATH=. python -m unittest tests.integration.roadmap.test_tracker_pipeline -v
```

Then run the synchronized build:

```bash
PYTHONPATH=. python roadmap_tracker.py
```

Expected root outputs:

```text
ROADMAP.md
ROADMAP_TRACKER.md
```

The package does not include or overwrite `ROADMAP.md`, `roadmap_data.py`,
`roadmap_frontend.py`, or any existing `roadmap/*.py` architecture module.
