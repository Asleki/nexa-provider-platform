# Nexa Provider Platform Roadmap Package

The `roadmap` package is the production roadmap engine for the **Nexa Provider Platform — Final Scope Engineering Roadmap**.

It converts the canonical records in `roadmap_data.py` into validated Python models and provides deterministic tools for:

- status handling;
- milestone modelling;
- structural validation;
- dependency analysis;
- roadmap queries;
- progress reporting;
- artifact generation;
- verification evidence;
- command execution; and
- immutable roadmap history.

## Canonical dataset

| Property | Value |
|---|---:|
| Roadmap version | `1.0.0` |
| Schema version | `1` |
| First milestone | `M001` |
| Last milestone | `M022.8` |
| Total records | **833** |
| Root milestones | **22** |
| Completed records | **76** |
| Planned records | **757** |
| Supported Python | **3.10+** |
| License | Proprietary |

The canonical data source remains:

```text
roadmap_data.py
```

The package does not replace the canonical dataset. It provides typed, deterministic, read-oriented operations over it.

---

## Package structure

```text
roadmap/
├── __init__.py
├── statuses.py
├── models.py
├── validation.py
├── dependencies.py
├── queries.py
├── progress.py
├── generator.py
├── verification.py
├── commands.py
├── history.py
└── README.md
```

| Module | Responsibility |
|---|---|
| `__init__.py` | Package metadata, version information, module registry, and Python compatibility helpers. |
| `statuses.py` | Canonical status enum, normalization, formatting, metadata, ordering, and status predicates. |
| `models.py` | Immutable roadmap metadata, milestone, and snapshot models. |
| `validation.py` | Field, record, collection, metadata, hierarchy, and full-roadmap validation. |
| `dependencies.py` | Dependency graphs, readiness, unresolved dependencies, cycles, paths, and topological ordering. |
| `queries.py` | Indexing, retrieval, searching, filtering, grouping, hierarchy traversal, and sorting. |
| `progress.py` | Completion counts, percentages, grouped progress, weighted progress, and next-work selection. |
| `generator.py` | Deterministic JSON, Markdown, Python, CSV, tree, manifest, and bundle generation. |
| `verification.py` | Verification states, evidence policies, findings, summaries, and strict verification checks. |
| `commands.py` | Command parser, command registry, built-in commands, formatting, and CLI entry point. |
| `history.py` | Immutable history entries, milestone checksums, snapshot differences, timelines, and tamper detection. |

---

## Installation and repository layout

The package is designed to live beside `roadmap_data.py`:

```text
nexa-provider-platform/
├── roadmap_data.py
├── roadmap.py
└── roadmap/
    ├── __init__.py
    ├── statuses.py
    ├── models.py
    ├── validation.py
    ├── dependencies.py
    ├── queries.py
    ├── progress.py
    ├── generator.py
    ├── verification.py
    ├── commands.py
    ├── history.py
    └── README.md
```

Run examples from the repository root so that both `roadmap_data` and `roadmap` are importable.

No third-party runtime dependency is required.

---

## Quick start

### Load the canonical roadmap

```python
import roadmap_data

from roadmap.models import RoadmapMetadata, RoadmapSnapshot, milestones_from_mappings

metadata = RoadmapMetadata(
    title=roadmap_data.ROADMAP_TITLE,
    version=roadmap_data.ROADMAP_VERSION,
    start=roadmap_data.ROADMAP_START,
    end=roadmap_data.ROADMAP_END,
    allowed_statuses=tuple(roadmap_data.ALLOWED_STATUSES),
    boundaries=getattr(roadmap_data, "ROADMAP_BOUNDARIES", {}),
)

milestones = milestones_from_mappings(roadmap_data.MILESTONES)
snapshot = RoadmapSnapshot(metadata=metadata, milestones=milestones)

assert len(snapshot.milestones) == 833
```

### Validate the roadmap

```python
from roadmap.validation import assert_valid, validate_snapshot

report = validate_snapshot(snapshot)

print(report.is_valid)
print(report.error_count)
print(report.warning_count)

assert_valid(snapshot)
```

### Query milestones

```python
from roadmap.queries import (
    get_by_number,
    get_children,
    get_roots,
    search,
)

milestone = get_by_number(snapshot, "M001")
roots = get_roots(snapshot)
children = get_children(snapshot, "M001")
matches = search(snapshot, "identity")

print(milestone.title)
print(len(roots))
print(len(children))
print(len(matches))
```

### Calculate progress

```python
from roadmap.progress import completion_percentage, summarize_progress

summary = summarize_progress(snapshot)

print(summary.total)
print(summary.complete)
print(summary.incomplete)
print(summary.percentage)

assert completion_percentage(snapshot) == summary.percentage
```

### Inspect dependencies

```python
from roadmap.dependencies import (
    dependency_summary,
    is_dependency_ready,
    topological_order,
)

summary = dependency_summary(snapshot, "M001")
ready = is_dependency_ready(snapshot, "M001")
ordered = topological_order(snapshot)

print(summary.direct_dependencies)
print(summary.unresolved_dependencies)
print(ready)
print(len(ordered))
```

### Verify evidence

```python
from roadmap.verification import (
    VerificationPolicy,
    summarize_verification,
    verify_collection,
)

policy = VerificationPolicy()
results = verify_collection(snapshot, policy=policy)
summary = summarize_verification(results)

print(summary.total)
print(summary.passing)
print(summary.failing)
```

The canonical records currently use `UNVERIFIED` as their default verification state unless evidence is supplied. Therefore, strict evidence policies can fail even when structural roadmap validation passes.

### Generate artifacts

```python
from pathlib import Path

from roadmap.generator import GenerationOptions, generate_bundle, write_bundle

options = GenerationOptions(
    include_metadata=True,
)

bundle = generate_bundle(
    snapshot,
    formats=("json", "markdown", "csv", "tree"),
    options=options,
)

written = write_bundle(
    bundle,
    Path("generated-roadmap"),
    overwrite=False,
)

for path in written:
    print(path)
```

Supported output formats are:

```text
json
markdown
md
python
py
csv
tree
txt
```

### Use the command layer

```python
from roadmap.commands import CommandContext, execute_command, format_result

context = CommandContext(snapshot=snapshot)

result = execute_command(
    ["show", "M001"],
    context=context,
)

print(format_result(result))
```

Built-in commands:

```text
help
summary
list
show
search
progress
dependencies
validate
verify
generate
```

The package also exposes a CLI-style entry point:

```bash
python -m roadmap.commands summary
python -m roadmap.commands show M001
python -m roadmap.commands search identity
python -m roadmap.commands progress
python -m roadmap.commands validate
python -m roadmap.commands verify
```

### Create and compare history

```python
from datetime import datetime, timezone
from dataclasses import replace

from roadmap.history import (
    RoadmapHistory,
    create_history_entry,
    diff_milestones,
    milestone_checksum,
    serialize_history,
)

before = snapshot.milestones[0]
after = replace(before, title=f"{before.title} Updated")

changes = diff_milestones(before, after)

entry = create_history_entry(
    after,
    before=before,
    actor="roadmap-maintainer",
    occurred_at=datetime.now(timezone.utc),
)

history = RoadmapHistory((entry,))

print(changes)
print(milestone_checksum(after))
print(serialize_history(history))
```

History objects are immutable and append-only. Serialized history includes a collection checksum and is rejected during deserialization when tampering changes the recorded payload without updating its checksum.

---

## Module reference

## `statuses.py`

Canonical status values are represented by `RoadmapStatus`.

Core helpers include:

```python
from roadmap.statuses import (
    RoadmapStatus,
    format_status,
    get_status_emoji,
    is_complete,
    is_open,
    normalize_status,
    sort_statuses,
    status_metadata,
)
```

Important collections:

- `ALLOWED_STATUS_VALUES`
- `STATUS_ORDER`
- `STATUS_LABELS`
- `STATUS_EMOJIS`
- `ACTIVE_STATUSES`
- `OPEN_STATUSES`
- `COMPLETE_STATUSES`
- `TERMINAL_STATUSES`
- `ACTIONABLE_STATUSES`

Always normalize external status values before comparing them:

```python
status = normalize_status("completed")
assert status is RoadmapStatus.COMPLETED
```

---

## `models.py`

Primary immutable models:

### `RoadmapMetadata`

Contains roadmap-level metadata such as:

- title;
- version;
- first and last milestone;
- allowed statuses; and
- optional boundaries.

### `Milestone`

Represents one canonical roadmap record with fields including:

- `record_id`
- `number`
- `title`
- `parent_number`
- `sequence`
- `depth`
- `semantic_path`
- `status`
- `dependencies`
- `priority`
- `commit_hash`
- `verification_state`
- `notes`
- `test_information`
- `passing_tests`
- `started_date`
- `completed_date`
- `metadata`

### `RoadmapSnapshot`

Combines `RoadmapMetadata` with an immutable tuple of milestones.

Conversion helpers:

```python
from roadmap.models import (
    milestone_to_mapping,
    milestones_from_mappings,
)
```

---

## `validation.py`

Validation is non-destructive. It returns structured issues rather than silently correcting data.

Primary functions:

```python
validate_mapping(...)
validate_milestone(...)
validate_collection(...)
validate_metadata(...)
validate_snapshot(...)
validate_roadmap(...)
assert_valid(...)
```

A `ValidationReport` contains issues with severity, code, message, record context, and field context.

Use `assert_valid` at release boundaries when invalid data must stop execution.

---

## `dependencies.py`

Dependency analysis supports:

- direct dependencies;
- direct dependents;
- transitive dependencies;
- transitive dependents;
- missing references;
- duplicate references;
- self-dependencies;
- unresolved dependencies;
- dependency readiness;
- blocking dependencies;
- graph cycle detection;
- dependency paths;
- dependency depth;
- topological ordering; and
- collection-wide dependency validation.

Errors use dedicated exception types:

- `RoadmapDependencyError`
- `MissingDependencyError`
- `DuplicateDependencyError`
- `DependencyCycleError`

---

## `queries.py`

Query functions accept a milestone collection or roadmap snapshot.

Common operations include:

```python
get_by_number(...)
get_by_record_id(...)
get_by_title(...)
search(...)
filter_by_status(...)
filter_by_parent(...)
filter_by_priority(...)
filter_by_dependency(...)
get_parent(...)
get_children(...)
get_ancestors(...)
get_descendants(...)
get_siblings(...)
get_roots(...)
group_by_status(...)
group_by_parent(...)
sort_by_sequence(...)
```

Build indexes once when repeatedly accessing the same collection:

```python
from roadmap.queries import build_number_index

number_index = build_number_index(snapshot)
milestone = number_index["M001"]
```

---

## `progress.py`

Progress calculations use immutable roadmap state and do not mutate status.

Key functions:

```python
progress_counts(...)
completion_count(...)
completion_percentage(...)
summarize_progress(...)
progress_by_status(...)
progress_by_parent(...)
progress_by_priority(...)
progress_by_depth(...)
weighted_progress(...)
next_incomplete(...)
```

`ProgressSummary` exposes:

- `total`
- `complete`
- `incomplete`
- `percentage`

---

## `generator.py`

Generation is deterministic: the same roadmap state and options produce the same content and checksums.

Primary abstractions:

- `GenerationOptions`
- `GeneratedArtifact`
- `GenerationBundle`

Rendering functions:

```python
render_json(...)
render_markdown(...)
render_python(...)
render_csv(...)
render_tree(...)
render_manifest(...)
```

Writing functions protect against accidental overwrite and unsafe output paths:

```python
write_artifact(...)
write_bundle(...)
```

Relevant exceptions:

- `RoadmapGenerationError`
- `UnsupportedFormatError`
- `UnsafeOutputPathError`
- `ExistingFileError`

---

## `verification.py`

Verification is separate from structural validation.

Structural validation answers:

> Is this roadmap record well-formed and internally consistent?

Verification answers:

> Is there sufficient evidence to treat this milestone as verified?

Evidence can include:

- commit hash;
- test information;
- passing-test count;
- verification state; and
- policy-required combinations of evidence.

Core types:

- `VerificationState`
- `VerificationPolicy`
- `VerificationFinding`
- `MilestoneVerification`
- `VerificationSummary`

Core operations:

```python
verify_milestone(...)
verify_collection(...)
verification_findings(...)
summarize_verification(...)
verification_state_counts(...)
verified_milestones(...)
unverified_milestones(...)
assert_verified(...)
```

---

## `commands.py`

The command layer provides a reusable command parser independent of a specific terminal framework.

Core abstractions:

- `CommandContext`
- `CommandDefinition`
- `CommandRegistry`
- `CommandResult`

Use `build_default_registry()` to create the standard registry, or register additional project-specific commands through a separate registry instance.

Primary execution path:

```python
parse_command_line(...)
execute_command(...)
format_result(...)
```

---

## `history.py`

History tracking is immutable, deterministic, and integrity-protected.

Core types:

- `FieldChange`
- `MilestoneHistoryEntry`
- `RoadmapHistory`
- `SnapshotDiff`

Core operations:

```python
milestone_checksum(...)
diff_milestones(...)
create_history_entry(...)
snapshot_diff(...)
history_from_snapshots(...)
status_transitions(...)
count_transitions(...)
serialize_history(...)
deserialize_history(...)
verify_history_integrity(...)
```

The history module does not write changes back to `roadmap_data.py`. It records and compares roadmap states so that another layer can decide how and where history should be persisted.

---

## Data integrity rules

The package follows these rules:

1. `roadmap_data.py` is the canonical source.
2. Canonical milestone identity is based on stable `record_id` and `number` values.
3. Models and history structures are immutable.
4. Query, progress, validation, dependency, verification, and generation operations do not mutate source records.
5. Generation output is deterministic.
6. Dependencies must resolve to known roadmap milestones.
7. Parent-child hierarchy must remain structurally valid.
8. Verification evidence is distinct from completion status.
9. History is append-only and checksum-protected.
10. Corrections should be explicit and reviewable rather than silently applied.

---

## Recommended workflow

### During development

```text
Edit canonical roadmap data
→ Load typed snapshot
→ Run structural validation
→ Run dependency validation
→ Review progress
→ Run verification policy
→ Generate artifacts
→ Record history
→ Commit reviewed changes
```

### Before a release

1. Compile every Python module.
2. Import every package module.
3. Validate all canonical records.
4. Verify unique IDs, numbers, parent links, and dependencies.
5. Run query, hierarchy, progress, generation, verification, command, and history tests.
6. Regenerate deterministic artifacts.
7. Compare artifact checksums.
8. Record the approved transition in history.
9. Commit the reviewed package and generated outputs.

---

## Testing

A minimum package test should verify the canonical counts:

```python
import roadmap_data

from roadmap.models import milestones_from_mappings
from roadmap.statuses import RoadmapStatus

records = milestones_from_mappings(roadmap_data.MILESTONES)

assert len(records) == 833
assert sum(record.is_root for record in records) == 22
assert sum(
    record.status is RoadmapStatus.COMPLETED
    for record in records
) == 76
assert sum(
    record.status is RoadmapStatus.PLANNED
    for record in records
) == 757
```

Compile the package:

```bash
python -m compileall roadmap roadmap.py roadmap_data.py
```

Run the project test suite from the repository root:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

When `pytest` is used by the repository:

```bash
python -m pytest
```

The exact test runner depends on the repository's test configuration.

---

## Extending the package

When adding a new module:

1. Keep the canonical dataset unchanged unless the roadmap itself is being edited.
2. Prefer immutable dataclasses and tuples.
3. Return structured results rather than printing inside core logic.
4. Keep serialization deterministic.
5. Use module-specific exception classes.
6. Add a complete `__all__` declaration.
7. Test against all 833 canonical records.
8. Compile and import the module before acceptance.
9. Produce a SHA-256 checksum for the final file.
10. Update this README and package metadata when the public API changes.

---

## Security and safety

The roadmap package is an engineering and planning component. It must not:

- execute production provider operations;
- bypass approval controls;
- treat roadmap completion as production verification;
- expose sensitive credentials through generated artifacts;
- silently rewrite canonical records; or
- accept tampered history as valid.

Generated files should be written only to approved repository paths.

---

## Package information

```python
import roadmap

print(roadmap.get_version())
print(roadmap.get_package_info())
print(roadmap.is_supported_python())
```

Current package metadata:

```text
Package: roadmap
Version: 1.0.0
API version: 1
Roadmap schema version: 1
Supported Python: 3.10+
Author: Nexa Provider Platform
License: Proprietary
```

---

## Status

All ten production Python modules have been generated, compiled, imported, and verified against the canonical 833-record roadmap dataset.

The package now contains:

```text
statuses.py
models.py
validation.py
dependencies.py
queries.py
progress.py
generator.py
verification.py
commands.py
history.py
README.md
```
