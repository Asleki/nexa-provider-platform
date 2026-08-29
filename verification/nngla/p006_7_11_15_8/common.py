"""Credential-safe operator helpers for P006.7.11.15.8."""
from __future__ import annotations

import getpass
import json
import os
from pathlib import Path
import subprocess

from registries.nngla.city_realization.persistence import PostgreSQLCityRealizationRepository
from registries.nngla.city_realization.postgis import PostGISCityRealizationEngine
from registries.nngla.city_realization.service import GovernedCityRealizationService


def repository_revision() -> str:
    configured = str(os.environ.get("NPP_REPOSITORY_REVISION", "")).strip()
    if configured:
        return configured
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if proc.returncode != 0 or not proc.stdout.strip():
        raise RuntimeError("repository revision unavailable; set NPP_REPOSITORY_REVISION")
    return proc.stdout.strip()


def connect_postgresql():
    try:
        import psycopg
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("psycopg is required for live PostgreSQL verification") from exc
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


def service(connection, *, environment_name: str, effective_date: str | None, revision: str | None = None):
    repository = PostgreSQLCityRealizationRepository(connection, environment_name=environment_name)
    postgis = PostGISCityRealizationEngine(connection)
    return GovernedCityRealizationService(
        repository,
        postgis,
        repository_revision=(revision or repository_revision()),
        effective_date=effective_date,
    )


def write_json(payload: object, output: str | None = None) -> None:
    encoded = json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
    print(encoded)
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded + "\n", encoding="utf-8")
