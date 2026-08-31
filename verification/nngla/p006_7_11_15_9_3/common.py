"""Credential-safe helpers for sequence-29 incremental TOWN publication."""
from __future__ import annotations

import getpass
import json
import os
from pathlib import Path
import subprocess

from registries.nngla.town_footprint_realization.incremental import (
    IncrementalTownPublicationService,
)

ROOT = Path(__file__).resolve().parents[3]
B19A = ROOT / "data/novegeo/nngla/spatial-fabric/bundle19a"
FOOTPRINT = B19A / "qualified/novegeo_settlement_footprints_v001.geojson"
REFERENCE = B19A / "qualified/novegeo_place_reference_points_v001.csv"
SUMMARY = B19A / "evidence/novegeo_place_spatialization_summary_v001.json"


def repository_revision() -> str:
    value = str(os.environ.get("NPP_REPOSITORY_REVISION", "")).strip()
    if value:
        return value
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError("repository revision is unavailable")
    return proc.stdout.strip()


def connect_postgresql():
    import psycopg

    required = ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER")
    missing = [name for name in required if not str(os.environ.get(name, "")).strip()]
    if missing:
        raise RuntimeError("missing PostgreSQL environment variables: " + ",".join(missing))
    password = getpass.getpass("PostgreSQL password: ")
    return psycopg.connect(
        host=os.environ["PGHOST"],
        port=os.environ["PGPORT"],
        dbname=os.environ["PGDATABASE"],
        user=os.environ["PGUSER"],
        password=password,
        sslmode=os.environ.get("PGSSLMODE", "require"),
        connect_timeout=int(os.environ.get("PGCONNECT_TIMEOUT", "30")),
    )


def service(connection, *, environment_name: str, effective_date: str | None = None, revision: str | None = None):
    return IncrementalTownPublicationService(
        connection,
        footprint_path=FOOTPRINT,
        reference_path=REFERENCE,
        summary_path=SUMMARY,
        environment_name=environment_name,
        repository_revision=revision or repository_revision(),
        effective_date=effective_date,
    )


def write_json(payload, output: str | None = None) -> None:
    text = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    print(text)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text + "\n", encoding="utf-8")
