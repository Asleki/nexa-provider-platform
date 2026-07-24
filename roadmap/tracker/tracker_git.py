"""
Git command adapter for explicit tracker evidence collection.

This module reads Git metadata only. It never commits, pushes, resets, checks
out, stages, or changes repository state.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from .models import CommitEvidence


class TrackerGitError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GitReader:
    repository: Path = Path(".")

    def _run(self, *args: str) -> str:
        command = ["git", "-C", str(self.repository), *args]
        try:
            result = subprocess.run(
                command,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
            )
        except (OSError, subprocess.CalledProcessError) as exc:
            raise TrackerGitError(f"git read command failed: {' '.join(command)}") from exc
        return result.stdout.strip()

    def read_commit(self, revision: str = "HEAD") -> CommitEvidence:
        raw = self._run(
            "show",
            "-s",
            "--format=%H%x1f%s%x1f%aI%x1f%an",
            revision,
        )
        parts = raw.split("\x1f")
        if len(parts) != 4:
            raise TrackerGitError("unexpected git commit output")
        return CommitEvidence(
            sha=parts[0],
            message=parts[1],
            committed_at=parts[2],
            author=parts[3],
        )

    def changed_files(self, revision: str = "HEAD") -> tuple[str, ...]:
        raw = self._run("show", "--pretty=", "--name-only", revision)
        return tuple(line for line in raw.splitlines() if line.strip())
