"""Data-driven migration-ready domain and batch-profile catalogue."""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

from .contracts import BatchProfile, DomainDisposition, DomainPlanEntry

ROOT = Path(__file__).resolve().parents[3]
DOMAIN_PLAN_PATH = (
    ROOT
    / "data"
    / "novegeo"
    / "nngla"
    / "migration-ready"
    / "source"
    / "00_manifest"
    / "novegeo_nngla_migration_ready_domain_plan_v001.csv"
)
BATCH_PROFILE_PATH = (
    ROOT
    / "data"
    / "novegeo"
    / "nngla"
    / "migration-ready"
    / "source"
    / "02_controlled_codes"
    / "novegeo_nngla_migration_batch_profiles_v001.csv"
)


def _rows(path: Path) -> tuple[dict[str, str], ...]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return tuple(dict(row) for row in csv.DictReader(handle))


def load_domain_plan(path: Path | None = None) -> tuple[DomainPlanEntry, ...]:
    source = path or DOMAIN_PLAN_PATH
    rows = _rows(source)
    entries = tuple(
        DomainPlanEntry(
            domain_key=row["domain_key"].strip(),
            source_path=row["source_path"].strip(),
            disposition=DomainDisposition(row["disposition"].strip()),
            expected_count=int(row["expected_count"]),
            canonical_target=row["canonical_target"].strip(),
            identity_policy=row["identity_policy"].strip(),
            notes=row.get("notes", "").strip(),
        )
        for row in rows
    )
    keys = [entry.domain_key for entry in entries]
    if len(keys) != len(set(keys)):
        raise ValueError("migration-ready domain keys must be unique")
    return entries


def load_batch_profiles(path: Path | None = None) -> dict[str, BatchProfile]:
    source = path or BATCH_PROFILE_PATH
    rows = _rows(source)
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["profile_id"].strip()].append(row)

    profiles: dict[str, BatchProfile] = {}
    for profile_id, values in grouped.items():
        ordered = sorted(values, key=lambda row: int(row["sequence_number"]))
        sequences = [int(row["sequence_number"]) for row in ordered]
        if sequences != list(range(1, len(ordered) + 1)):
            raise ValueError(f"batch profile {profile_id} sequence numbers must be contiguous from 1")
        totals = {int(row["expected_total"]) for row in ordered}
        purposes = {row["purpose"].strip() for row in ordered}
        if len(totals) != 1 or len(purposes) != 1:
            raise ValueError(f"batch profile {profile_id} metadata must remain stable across rows")
        profiles[profile_id] = BatchProfile(
            profile_id=profile_id,
            expected_total=next(iter(totals)),
            batch_sizes=tuple(int(row["batch_size"]) for row in ordered),
            purpose=next(iter(purposes)),
        )
    return profiles


def get_batch_profile(profile_id: str, path: Path | None = None) -> BatchProfile:
    try:
        return load_batch_profiles(path)[profile_id]
    except KeyError as exc:
        raise KeyError(f"unknown NNGLA migration-ready batch profile: {profile_id}") from exc


__all__ = [
    "ROOT",
    "DOMAIN_PLAN_PATH",
    "BATCH_PROFILE_PATH",
    "load_domain_plan",
    "load_batch_profiles",
    "get_batch_profile",
]
