"""
Deterministic roadmap artifact generation for the Nexa Provider Platform.

This module converts immutable roadmap models into stable JSON, Markdown,
Python, CSV, text-tree, and manifest artifacts. It provides pure renderers,
safe file writers, output bundles, checksums, and round-trip helpers.

Generation is deterministic: identical source data and options produce
identical text and SHA-256 checksums.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import pprint
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Iterable, Mapping, Sequence

from .models import (
    Milestone,
    RoadmapMetadata,
    RoadmapSnapshot,
)
from .queries import (
    MilestoneSource,
    all_milestones,
    build_number_index,
)
from .statuses import RoadmapStatus


class RoadmapGenerationError(ValueError):
    """Base exception for roadmap artifact generation errors."""


class UnsupportedFormatError(RoadmapGenerationError):
    """Raised when an unsupported output format is requested."""


class UnsafeOutputPathError(RoadmapGenerationError):
    """Raised when an output path escapes its configured directory."""


class ExistingFileError(RoadmapGenerationError):
    """Raised when overwrite is disabled and a target file exists."""


@dataclass(frozen=True, slots=True)
class GenerationOptions:
    """Immutable rendering options shared by all generators."""

    indent: int = 2
    sort_records: bool = True
    include_metadata: bool = True
    include_empty_fields: bool = True
    ensure_ascii: bool = False
    newline: str = "\n"
    markdown_heading_level: int = 1
    markdown_include_details: bool = True
    markdown_include_status: bool = True
    csv_include_metadata: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.indent, bool) or not isinstance(self.indent, int):
            raise TypeError("indent must be an integer")
        if self.indent < 0:
            raise RoadmapGenerationError("indent cannot be negative")
        if self.newline not in {"\n", "\r\n"}:
            raise RoadmapGenerationError(
                "newline must be either LF or CRLF"
            )
        if (
            isinstance(self.markdown_heading_level, bool)
            or not isinstance(self.markdown_heading_level, int)
        ):
            raise TypeError("markdown_heading_level must be an integer")
        if not 1 <= self.markdown_heading_level <= 6:
            raise RoadmapGenerationError(
                "markdown_heading_level must be between 1 and 6"
            )


@dataclass(frozen=True, slots=True)
class GeneratedArtifact:
    """One immutable generated artifact."""

    name: str
    format: str
    content: str
    sha256: str
    size_bytes: int
    record_count: int

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise RoadmapGenerationError("artifact name cannot be blank")
        if not self.format.strip():
            raise RoadmapGenerationError("artifact format cannot be blank")
        expected = hashlib.sha256(
            self.content.encode("utf-8")
        ).hexdigest()
        if self.sha256 != expected:
            raise RoadmapGenerationError(
                "artifact sha256 does not match content"
            )
        if self.size_bytes != len(self.content.encode("utf-8")):
            raise RoadmapGenerationError(
                "artifact size_bytes does not match content"
            )
        if self.record_count < 0:
            raise RoadmapGenerationError(
                "artifact record_count cannot be negative"
            )


@dataclass(frozen=True, slots=True)
class GenerationBundle:
    """Immutable collection of generated artifacts."""

    artifacts: tuple[GeneratedArtifact, ...]

    def __post_init__(self) -> None:
        artifacts = tuple(self.artifacts)
        names = [item.name for item in artifacts]
        if len(names) != len(set(names)):
            raise RoadmapGenerationError(
                "artifact names must be unique"
            )
        object.__setattr__(self, "artifacts", artifacts)

    @property
    def total_artifacts(self) -> int:
        return len(self.artifacts)

    @property
    def total_bytes(self) -> int:
        return sum(item.size_bytes for item in self.artifacts)

    def by_name(self) -> Mapping[str, GeneratedArtifact]:
        return MappingProxyType({
            item.name: item for item in self.artifacts
        })

    def manifest(self) -> tuple[dict[str, object], ...]:
        return tuple({
            "name": item.name,
            "format": item.format,
            "sha256": item.sha256,
            "size_bytes": item.size_bytes,
            "record_count": item.record_count,
        } for item in self.artifacts)


SUPPORTED_FORMATS = frozenset({
    "json",
    "markdown",
    "md",
    "python",
    "py",
    "csv",
    "tree",
    "txt",
})


def _newline(text: str, newline: str) -> str:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    if newline != "\n":
        normalized = normalized.replace("\n", newline)
    return normalized


def _ordered_records(
    source: MilestoneSource,
    *,
    sort_records: bool,
) -> tuple[Milestone, ...]:
    records = all_milestones(source)
    if not sort_records:
        return records
    return tuple(sorted(
        records,
        key=lambda item: (
            item.sequence,
            item.number,
            item.record_id,
        ),
    ))


def _json_safe(value: Any) -> Any:
    if isinstance(value, RoadmapStatus):
        return value.value
    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    return value


def metadata_to_mapping(
    metadata: RoadmapMetadata,
) -> dict[str, object]:
    """Convert metadata to a JSON-safe mapping."""

    if not isinstance(metadata, RoadmapMetadata):
        raise TypeError("metadata must be RoadmapMetadata")
    return {
        "title": metadata.title,
        "version": metadata.version,
        "start": metadata.start,
        "end": metadata.end,
        "allowed_statuses": [
            status.value for status in metadata.allowed_statuses
        ],
        "boundaries": _json_safe(metadata.boundaries),
    }


def milestone_to_mapping(
    milestone: Milestone,
    *,
    include_metadata: bool = True,
    include_empty_fields: bool = True,
) -> dict[str, object]:
    """Convert one milestone to a stable JSON-safe mapping."""

    if not isinstance(milestone, Milestone):
        raise TypeError("milestone must be a Milestone")

    mapping = milestone.to_mapping(
        include_metadata=include_metadata,
    )
    result = {
        key: _json_safe(value)
        for key, value in mapping.items()
    }
    if not include_empty_fields:
        result = {
            key: value
            for key, value in result.items()
            if value not in (None, "", [], {}, ())
        }
    return result


def roadmap_to_mapping(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    metadata: RoadmapMetadata | None = None,
    options: GenerationOptions | None = None,
) -> dict[str, object]:
    """Convert a roadmap source to a deterministic mapping."""

    active = options or GenerationOptions()

    if isinstance(source, RoadmapSnapshot):
        records = _ordered_records(
            source.milestones,
            sort_records=active.sort_records,
        )
        resolved_metadata = source.metadata
    else:
        records = _ordered_records(
            source,
            sort_records=active.sort_records,
        )
        resolved_metadata = metadata

    result: dict[str, object] = {
        "milestones": [
            milestone_to_mapping(
                item,
                include_metadata=False,
                include_empty_fields=active.include_empty_fields,
            )
            for item in records
        ]
    }
    if active.include_metadata and resolved_metadata is not None:
        result = {
            "roadmap": metadata_to_mapping(resolved_metadata),
            **result,
        }
    return result


def render_json(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    metadata: RoadmapMetadata | None = None,
    options: GenerationOptions | None = None,
) -> str:
    """Render deterministic UTF-8 JSON."""

    active = options or GenerationOptions()
    payload = roadmap_to_mapping(
        source,
        metadata=metadata,
        options=active,
    )
    text = json.dumps(
        payload,
        indent=active.indent,
        ensure_ascii=active.ensure_ascii,
        sort_keys=False,
    )
    return _newline(text + "\n", active.newline)


def _python_literal(value: object) -> str:
    return pprint.pformat(
        value,
        width=88,
        sort_dicts=False,
        compact=False,
    )


def render_python(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    metadata: RoadmapMetadata | None = None,
    options: GenerationOptions | None = None,
    module_docstring: str = (
        "Generated roadmap data. Do not edit by hand."
    ),
) -> str:
    """Render a standalone importable Python data module."""

    active = options or GenerationOptions()

    if isinstance(source, RoadmapSnapshot):
        records = _ordered_records(
            source.milestones,
            sort_records=active.sort_records,
        )
        resolved_metadata = source.metadata
    else:
        records = _ordered_records(
            source,
            sort_records=active.sort_records,
        )
        resolved_metadata = metadata

    mappings = tuple(
        milestone_to_mapping(
            item,
            include_metadata=False,
            include_empty_fields=active.include_empty_fields,
        )
        for item in records
    )

    lines = [
        f'"""{module_docstring}"""',
        "",
        "from __future__ import annotations",
        "",
    ]

    if active.include_metadata and resolved_metadata is not None:
        meta = metadata_to_mapping(resolved_metadata)
        lines.extend([
            f"ROADMAP_TITLE = {_python_literal(meta['title'])}",
            f"ROADMAP_VERSION = {_python_literal(meta['version'])}",
            f"ROADMAP_START = {_python_literal(meta['start'])}",
            f"ROADMAP_END = {_python_literal(meta['end'])}",
            (
                "ALLOWED_STATUSES = "
                + _python_literal(tuple(meta["allowed_statuses"]))
            ),
            (
                "ROADMAP_BOUNDARIES = "
                + _python_literal(meta["boundaries"])
            ),
            "",
        ])

    lines.extend([
        "MILESTONES = (",
    ])
    for mapping in mappings:
        literal = _python_literal(mapping)
        indented = "\n".join(
            "    " + line for line in literal.splitlines()
        )
        lines.append(indented + ",")
    lines.extend([
        ")",
        "",
        f"TOTAL_MILESTONES = {len(records)}",
        "",
        "__all__ = (",
        '    "MILESTONES",',
        '    "TOTAL_MILESTONES",',
    ])
    if active.include_metadata and resolved_metadata is not None:
        lines.extend([
            '    "ROADMAP_TITLE",',
            '    "ROADMAP_VERSION",',
            '    "ROADMAP_START",',
            '    "ROADMAP_END",',
            '    "ALLOWED_STATUSES",',
            '    "ROADMAP_BOUNDARIES",',
        ])
    lines.extend([
        ")",
        "",
    ])

    return _newline("\n".join(lines), active.newline)


def _markdown_escape(value: object) -> str:
    text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\n", "<br>")
    )


def render_markdown(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    metadata: RoadmapMetadata | None = None,
    options: GenerationOptions | None = None,
) -> str:
    """Render a hierarchical Markdown roadmap."""

    active = options or GenerationOptions()

    if isinstance(source, RoadmapSnapshot):
        records = _ordered_records(
            source.milestones,
            sort_records=active.sort_records,
        )
        resolved_metadata = source.metadata
    else:
        records = _ordered_records(
            source,
            sort_records=active.sort_records,
        )
        resolved_metadata = metadata

    base_level = active.markdown_heading_level
    lines: list[str] = []

    if active.include_metadata and resolved_metadata is not None:
        lines.extend([
            "#" * base_level + " " + resolved_metadata.title,
            "",
            f"- **Version:** {resolved_metadata.version}",
            f"- **Range:** {resolved_metadata.start} → {resolved_metadata.end}",
            (
                "- **Allowed statuses:** "
                + ", ".join(
                    status.value
                    for status in resolved_metadata.allowed_statuses
                )
            ),
            f"- **Milestones:** {len(records)}",
            "",
        ])
        item_base = min(base_level + 1, 6)
    else:
        item_base = base_level

    for item in records:
        level = min(item_base + item.depth, 6)
        status_text = (
            f" — `{item.status.value}`"
            if active.markdown_include_status
            else ""
        )
        lines.append(
            "#" * level
            + f" {item.number} — {item.title}{status_text}"
        )
        lines.append("")

        if active.markdown_include_details:
            lines.extend([
                f"- **Record ID:** `{item.record_id}`",
                f"- **Sequence:** {item.sequence}",
                f"- **Depth:** {item.depth}",
                f"- **Semantic path:** {_markdown_escape(item.semantic_path)}",
                f"- **Priority:** `{item.priority}`",
            ])
            if item.parent_number is not None:
                lines.append(
                    f"- **Parent:** `{item.parent_number}`"
                )
            if item.dependencies:
                lines.append(
                    "- **Dependencies:** "
                    + ", ".join(
                        f"`{number}`"
                        for number in item.dependencies
                    )
                )
            if item.verification_state:
                lines.append(
                    "- **Verification:** "
                    f"`{item.verification_state}`"
                )
            if item.commit_hash:
                lines.append(
                    f"- **Commit:** `{item.commit_hash}`"
                )
            if item.started_date:
                lines.append(
                    f"- **Started:** {item.started_date}"
                )
            if item.completed_date:
                lines.append(
                    f"- **Completed:** {item.completed_date}"
                )
            if item.passing_tests is not None:
                lines.append(
                    f"- **Passing tests:** {item.passing_tests}"
                )
            if item.notes:
                lines.append("- **Notes:**")
                lines.extend(
                    f"  - {_markdown_escape(note)}"
                    for note in item.notes
                )
            if item.test_information:
                lines.append("- **Test information:**")
                lines.extend(
                    f"  - {_markdown_escape(info)}"
                    for info in item.test_information
                )
            lines.append("")

    return _newline("\n".join(lines).rstrip() + "\n", active.newline)


CSV_FIELDS = (
    "record_id",
    "number",
    "title",
    "parent_number",
    "sequence",
    "depth",
    "semantic_path",
    "status",
    "dependencies",
    "priority",
    "commit_hash",
    "verification_state",
    "notes",
    "test_information",
    "passing_tests",
    "started_date",
    "completed_date",
)


def render_csv(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    options: GenerationOptions | None = None,
) -> str:
    """Render roadmap records as RFC-compatible CSV."""

    active = options or GenerationOptions()
    records = (
        source.milestones
        if isinstance(source, RoadmapSnapshot)
        else source
    )
    records = _ordered_records(
        records,
        sort_records=active.sort_records,
    )

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(
        buffer,
        fieldnames=CSV_FIELDS,
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()

    for item in records:
        mapping = milestone_to_mapping(
            item,
            include_metadata=False,
            include_empty_fields=True,
        )
        row = {
            field: mapping.get(field)
            for field in CSV_FIELDS
        }
        row["dependencies"] = json.dumps(
            row["dependencies"],
            ensure_ascii=active.ensure_ascii,
        )
        row["notes"] = json.dumps(
            row["notes"],
            ensure_ascii=active.ensure_ascii,
        )
        row["test_information"] = json.dumps(
            row["test_information"],
            ensure_ascii=active.ensure_ascii,
        )
        writer.writerow(row)

    return _newline(buffer.getvalue(), active.newline)


def render_tree(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    options: GenerationOptions | None = None,
    include_status: bool = True,
) -> str:
    """Render a deterministic Unicode hierarchy tree."""

    active = options or GenerationOptions()
    records = (
        source.milestones
        if isinstance(source, RoadmapSnapshot)
        else source
    )
    ordered = _ordered_records(
        records,
        sort_records=active.sort_records,
    )

    children: dict[str | None, list[Milestone]] = {}
    for item in ordered:
        children.setdefault(item.parent_number, []).append(item)

    for values in children.values():
        values.sort(
            key=lambda item: (
                item.sequence,
                item.number,
            )
        )

    lines: list[str] = []

    def walk(
        parent_number: str | None,
        prefix: str,
    ) -> None:
        siblings = children.get(parent_number, [])
        for index, item in enumerate(siblings):
            last = index == len(siblings) - 1
            connector = "└── " if last else "├── "
            status = (
                f" [{item.status.value}]"
                if include_status
                else ""
            )
            lines.append(
                f"{prefix}{connector}{item.number} — "
                f"{item.title}{status}"
            )
            walk(
                item.number,
                prefix + ("    " if last else "│   "),
            )

    roots = children.get(None, [])
    for index, root in enumerate(roots):
        status = (
            f" [{root.status.value}]"
            if include_status
            else ""
        )
        lines.append(
            f"{root.number} — {root.title}{status}"
        )
        walk(
            root.number,
            "" if index == len(roots) - 1 else "",
        )

    return _newline("\n".join(lines) + ("\n" if lines else ""), active.newline)


def sha256_text(content: str) -> str:
    """Return the UTF-8 SHA-256 checksum for text."""

    if not isinstance(content, str):
        raise TypeError("content must be a string")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def make_artifact(
    name: str,
    format: str,
    content: str,
    *,
    record_count: int,
) -> GeneratedArtifact:
    """Construct a validated generated artifact."""

    normalized = format.strip().lower()
    if normalized not in SUPPORTED_FORMATS:
        raise UnsupportedFormatError(
            f"Unsupported format {format!r}"
        )
    return GeneratedArtifact(
        name=name,
        format=normalized,
        content=content,
        sha256=sha256_text(content),
        size_bytes=len(content.encode("utf-8")),
        record_count=record_count,
    )


def generate_artifact(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    format: str,
    name: str | None = None,
    metadata: RoadmapMetadata | None = None,
    options: GenerationOptions | None = None,
) -> GeneratedArtifact:
    """Generate one artifact in a supported format."""

    normalized = format.strip().lower()
    records = (
        source.milestones
        if isinstance(source, RoadmapSnapshot)
        else all_milestones(source)
    )
    count = len(records)

    if normalized == "json":
        content = render_json(
            source,
            metadata=metadata,
            options=options,
        )
        default_name = "roadmap.json"
    elif normalized in {"markdown", "md"}:
        content = render_markdown(
            source,
            metadata=metadata,
            options=options,
        )
        default_name = "roadmap.md"
    elif normalized in {"python", "py"}:
        content = render_python(
            source,
            metadata=metadata,
            options=options,
        )
        default_name = "roadmap_data.py"
    elif normalized == "csv":
        content = render_csv(
            source,
            options=options,
        )
        default_name = "roadmap.csv"
    elif normalized in {"tree", "txt"}:
        content = render_tree(
            source,
            options=options,
        )
        default_name = "roadmap.txt"
    else:
        raise UnsupportedFormatError(
            f"Unsupported format {format!r}"
        )

    return make_artifact(
        name or default_name,
        normalized,
        content,
        record_count=count,
    )


def generate_bundle(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    formats: Sequence[str] = (
        "json",
        "markdown",
        "python",
        "csv",
        "tree",
    ),
    metadata: RoadmapMetadata | None = None,
    options: GenerationOptions | None = None,
) -> GenerationBundle:
    """Generate a deterministic multi-format artifact bundle."""

    artifacts = tuple(
        generate_artifact(
            source,
            format=format,
            metadata=metadata,
            options=options,
        )
        for format in formats
    )
    return GenerationBundle(artifacts)


def render_manifest(
    bundle: GenerationBundle,
    *,
    indent: int = 2,
    ensure_ascii: bool = False,
    newline: str = "\n",
) -> str:
    """Render a JSON manifest for a generation bundle."""

    if not isinstance(bundle, GenerationBundle):
        raise TypeError("bundle must be a GenerationBundle")
    payload = {
        "total_artifacts": bundle.total_artifacts,
        "total_bytes": bundle.total_bytes,
        "artifacts": bundle.manifest(),
    }
    text = json.dumps(
        payload,
        indent=indent,
        ensure_ascii=ensure_ascii,
    )
    return _newline(text + "\n", newline)


def _safe_target(
    directory: Path,
    name: str,
) -> Path:
    if not name or Path(name).name != name:
        raise UnsafeOutputPathError(
            "artifact name must be a simple filename"
        )
    base = directory.resolve()
    target = (base / name).resolve()
    if target.parent != base:
        raise UnsafeOutputPathError(
            "output path escapes target directory"
        )
    return target


def write_artifact(
    artifact: GeneratedArtifact,
    directory: str | Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Write one artifact using UTF-8 and return its path."""

    if not isinstance(artifact, GeneratedArtifact):
        raise TypeError("artifact must be GeneratedArtifact")
    directory_path = Path(directory)
    directory_path.mkdir(parents=True, exist_ok=True)
    target = _safe_target(directory_path, artifact.name)

    if target.exists() and not overwrite:
        raise ExistingFileError(
            f"Refusing to overwrite existing file: {target}"
        )
    target.write_text(
        artifact.content,
        encoding="utf-8",
        newline="",
    )

    written_hash = hashlib.sha256(
        target.read_bytes()
    ).hexdigest()
    if written_hash != artifact.sha256:
        raise RoadmapGenerationError(
            f"Written checksum mismatch for {target}"
        )
    return target


def write_bundle(
    bundle: GenerationBundle,
    directory: str | Path,
    *,
    overwrite: bool = False,
    include_manifest: bool = True,
    manifest_name: str = "manifest.json",
) -> tuple[Path, ...]:
    """Write all bundle artifacts and an optional manifest."""

    if not isinstance(bundle, GenerationBundle):
        raise TypeError("bundle must be a GenerationBundle")

    paths = [
        write_artifact(
            artifact,
            directory,
            overwrite=overwrite,
        )
        for artifact in bundle.artifacts
    ]

    if include_manifest:
        manifest_content = render_manifest(bundle)
        manifest_artifact = make_artifact(
            manifest_name,
            "json",
            manifest_content,
            record_count=0,
        )
        paths.append(
            write_artifact(
                manifest_artifact,
                directory,
                overwrite=overwrite,
            )
        )
    return tuple(paths)


def canonical_checksum(
    source: MilestoneSource | RoadmapSnapshot,
    *,
    metadata: RoadmapMetadata | None = None,
) -> str:
    """Return the checksum of canonical compact JSON."""

    options = GenerationOptions(
        indent=0,
        sort_records=True,
        include_metadata=True,
        include_empty_fields=True,
        ensure_ascii=False,
    )
    return sha256_text(
        render_json(
            source,
            metadata=metadata,
            options=options,
        )
    )


__all__ = (
    "CSV_FIELDS",
    "ExistingFileError",
    "GeneratedArtifact",
    "GenerationBundle",
    "GenerationOptions",
    "RoadmapGenerationError",
    "SUPPORTED_FORMATS",
    "UnsafeOutputPathError",
    "UnsupportedFormatError",
    "canonical_checksum",
    "generate_artifact",
    "generate_bundle",
    "make_artifact",
    "metadata_to_mapping",
    "milestone_to_mapping",
    "render_csv",
    "render_json",
    "render_manifest",
    "render_markdown",
    "render_python",
    "render_tree",
    "roadmap_to_mapping",
    "sha256_text",
    "write_artifact",
    "write_bundle",
)
