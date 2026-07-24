"""
Commit evidence helpers for tracker records.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Iterable

from .models import CommitEvidence, TrackerRecord


def add_commit(
    record: TrackerRecord,
    commit: CommitEvidence,
    *,
    updated_at: str,
) -> TrackerRecord:
    existing = {item.sha for item in record.commits}
    if commit.sha in existing:
        return record
    return replace(
        record,
        commits=tuple(record.commits) + (commit,),
        updated_at=updated_at,
    )


def unique_commits(records: Iterable[TrackerRecord]) -> tuple[CommitEvidence, ...]:
    by_sha: dict[str, CommitEvidence] = {}
    for record in records:
        for commit in record.commits:
            by_sha.setdefault(commit.sha, commit)
    return tuple(
        sorted(by_sha.values(), key=lambda item: (item.committed_at, item.sha))
    )
