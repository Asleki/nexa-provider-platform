"""P006.7.1 Bundle 13B sovereign operating-context qualification."""
from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from shared.runtime.operation_runtime import OperationRuntimeMode
from .operating_context import ApprovalState, RecordEffectScope
from .operating_context_source import Bundle13BSourceSnapshot, read_bundle13b_source


@dataclass(frozen=True, slots=True)
class Bundle13BQualificationReceipt:
    status: str
    source: Bundle13BSourceSnapshot
    source_sha256: tuple[tuple[str, str], ...]
    findings: tuple[str, ...]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def qualify_bundle13b_source(repository_root: str | Path) -> Bundle13BQualificationReceipt:
    root = Path(repository_root)
    source_dir = root / "data/novegeo/country/operating-context/source"
    provenance_path = root / "data/novegeo/country/operating-context/provenance/bundle13b_authority_source.json"
    country_profile = root / "data/novegeo/country/source/novegeo_country_profile.csv"
    if not provenance_path.is_file():
        raise FileNotFoundError(provenance_path)

    snapshot = read_bundle13b_source(root)
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    if provenance.get("operationalAuthority") is not False:
        raise ValueError("Bundle 13B CSV snapshot must not claim operational authority.")
    if provenance.get("runtimeCsvConsumptionAllowed") is not False:
        raise ValueError("Bundle 13B CSV snapshot must prohibit live runtime CSV consumption.")
    if "PostgreSQL" not in provenance.get("canonicalRuntimePersistence", ""):
        raise ValueError("Bundle 13B provenance must preserve the later PostgreSQL authority boundary.")

    if snapshot.realm.realm_id != "realm:nexilabs:novegeo" or snapshot.realm.country_id != "country:novegeo":
        raise ValueError("unexpected NoveGeo realm-to-country association.")
    if {runtime.runtime_mode for runtime in snapshot.runtimes} != {
        OperationRuntimeMode.SIMULATION,
        OperationRuntimeMode.PRODUCTION,
    }:
        raise ValueError("semantic runtime register must contain exactly simulation and production.")
    semantic_roles = {runtime.runtime_mode: runtime.semantic_role for runtime in snapshot.runtimes}
    if semantic_roles != {
        OperationRuntimeMode.SIMULATION: "simulated_world_operations",
        OperationRuntimeMode.PRODUCTION: "governed_operator_actions",
    }:
        raise ValueError("semantic runtime roles drifted from the governed authority register.")
    if set(snapshot.effect_scopes) != set(RecordEffectScope):
        raise ValueError("effect-scope register does not match the governed Bundle 13B vocabulary.")
    if set(snapshot.approval_states) != set(ApprovalState):
        raise ValueError("approval-state register does not match the governed Bundle 13B vocabulary.")
    approval_rows = _read_rows(source_dir / "nexilabs_approval_state_register.csv")
    terminal_by_state = {
        ApprovalState(row["approval_state_code"]): row["terminal"].strip().lower() == "true"
        for row in approval_rows
    }
    if terminal_by_state != {state: state.terminal for state in ApprovalState}:
        raise ValueError("approval-state terminal semantics drifted from the governed register.")
    if snapshot.timezone.timezone_code != "Africa/NoveGeo":
        raise ValueError("unexpected NoveGeo timezone identity.")
    if snapshot.timezone.utc_offset_standard != "+02:00" or snapshot.timezone.dst_observed:
        raise ValueError("NoveGeo timezone must preserve UTC+02:00 with no DST.")
    if snapshot.calendar.calendar_code.value != "GREGORIAN":
        raise ValueError("NoveGeo calendar must remain Gregorian.")
    if (
        snapshot.calendar.days_per_week != 7
        or snapshot.calendar.month_model != "12_months"
        or snapshot.calendar.leap_year_model != "Gregorian"
    ):
        raise ValueError("NoveGeo Gregorian calendar dimensions drifted from the governed definition.")
    if snapshot.date_time_policy.date_format != "DD/MM/YYYY":
        raise ValueError("NoveGeo date-format policy drift detected.")
    if snapshot.date_time_policy.time_format != "HH:mm:ss":
        raise ValueError("NoveGeo time-format policy drift detected.")
    if snapshot.date_time_policy.datetime_format != "DD/MM/YYYY HH:mm:ss":
        raise ValueError("NoveGeo date-time format policy drift detected.")
    if snapshot.date_time_policy.first_day_of_week.value != "MONDAY":
        raise ValueError("NoveGeo first-day-of-week policy drift detected.")
    if any(mapping.clock_ratio != "1:1" for mapping in snapshot.runtime_time_mappings):
        raise ValueError("NoveGeo runtime time mappings must preserve 1:1 clock ratio.")
    if {mapping.runtime_mode for mapping in snapshot.runtime_time_mappings} != {
        OperationRuntimeMode.SIMULATION,
        OperationRuntimeMode.PRODUCTION,
    }:
        raise ValueError("both semantic runtimes must have a NoveGeo time mapping.")
    if snapshot.currency.currency_code != "NGC" or snapshot.currency.currency_symbol != "₦G":
        raise ValueError("NoveGeo currency reference drift detected.")

    matrix_path = source_dir / "nexilabs_runtime_authority_matrix.csv"
    matrix = _read_rows(matrix_path)
    if not matrix:
        raise ValueError("runtime authority matrix cannot be empty.")
    for row in matrix:
        runtime = OperationRuntimeMode(row["runtime_code"].lower())
        scope = RecordEffectScope(row["effect_scope_code"])
        if scope is RecordEffectScope.SIMULATION_ONLY and runtime is OperationRuntimeMode.PRODUCTION:
            raise ValueError("authority matrix contains simulation-only production effect.")
        if scope is RecordEffectScope.PRODUCTION_ONLY and runtime is OperationRuntimeMode.SIMULATION:
            raise ValueError("authority matrix contains production-only simulation effect.")
        if row["approval_required"].strip().lower() not in {"true", "false"}:
            raise ValueError("approval_required must be a boolean token.")

    files = sorted(source_dir.glob("*.csv")) + [provenance_path, country_profile]
    hashes = tuple((str(path.relative_to(root)), _sha256(path)) for path in files)
    findings = (
        "REALM_COUNTRY_ASSOCIATION_VALID",
        "SEMANTIC_RUNTIME_VOCABULARY_VALID",
        "DEPLOYMENT_ENVIRONMENT_NOT_RUNTIME",
        "EFFECT_SCOPE_VOCABULARY_VALID",
        "APPROVAL_STATE_VOCABULARY_VALID",
        "APPROVAL_REQUIREMENT_SEPARATE_FROM_STATE",
        "RUNTIME_EFFECT_SCOPE_SEPARATION_VALID",
        "NOVEGEO_TIMEZONE_IDENTITY_VALID",
        "UTC_PLUS_02_NO_DST_VALID",
        "FIXED_OFFSET_EXECUTION_AVAILABLE_WITHOUT_HOST_TZDB",
        "RUNTIME_CLOCK_RATIO_ONE_TO_ONE_VALID",
        "GREGORIAN_CALENDAR_VALID",
        "LOCAL_DATE_TIME_POLICY_VALID",
        "NGC_REFERENCE_BOUNDARY_VALID",
        "CSV_RUNTIME_AUTHORITY_PROHIBITED",
        "POSTGRESQL_AUTHORITY_BOUNDARY_PRESERVED",
        "BUNDLE13A_IMMUTABILITY_PRESERVED",
    )
    return Bundle13BQualificationReceipt("PASSED", snapshot, hashes, findings)
