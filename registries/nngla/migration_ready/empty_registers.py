"""Readiness checks for intentionally empty NNGLA Day-Zero operational registers."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

from .contracts import EmptyRegisterStatus


@dataclass(frozen=True, slots=True)
class EmptyRegisterContract:
    domain_key: str
    historical_path: str
    operational_path: str
    target_relation: str
    required_operational_fields: frozenset[str]


EMPTY_REGISTER_CONTRACTS = (
    EmptyRegisterContract(
        "addresses",
        "data/novegeo/nngla/geometry-roads-addresses/source/06_roads_addresses/address_reference_candidates.csv",
        "data/novegeo/nngla/geometry-roads-addresses/source/06_roads_addresses/address_reference_candidates_v002.csv",
        "geography.nngla_address",
        frozenset({
            "address_candidate_id", "road_id", "road_segment_id", "address_series_id",
            "site_id", "display_address_number", "place_id", "administrative_area_id",
            "parcel_id", "allocation_status", "address_status", "runtime_effect_scope",
        }),
    ),
    EmptyRegisterContract(
        "parcels",
        "data/novegeo/nngla/cadastre-titles-state-land/source/07_land/parcel_bootstrap.csv",
        "data/novegeo/nngla/cadastre-titles-state-land/source/07_land/parcel_bootstrap_v002.csv",
        "geography.nngla_parcel",
        frozenset({
            "parcel_id", "parent_parcel_id", "cadastral_series", "parcel_sequence",
            "parcel_status", "geometry_reference", "survey_status", "runtime_effect_scope",
        }),
    ),
    EmptyRegisterContract(
        "titles",
        "data/novegeo/nngla/cadastre-titles-state-land/source/07_land/title_bootstrap.csv",
        "data/novegeo/nngla/cadastre-titles-state-land/source/07_land/title_bootstrap_v002.csv",
        "geography.nngla_title",
        frozenset({
            "title_id", "parcel_id", "title_type_code", "tenure_type_code",
            "holder_reference", "title_status", "runtime_effect_scope",
        }),
    ),
    EmptyRegisterContract(
        "state-land",
        "data/novegeo/nngla/cadastre-titles-state-land/source/07_land/state_land_bootstrap.csv",
        "data/novegeo/nngla/cadastre-titles-state-land/source/07_land/state_land_bootstrap_v002.csv",
        "geography.nngla_state_land",
        frozenset({
            "state_land_record_id", "parcel_id", "state_land_category_code",
            "administrative_area_id", "status", "runtime_effect_scope",
        }),
    ),
    EmptyRegisterContract(
        "survey-control",
        "data/novegeo/nngla/geometry-roads-addresses/source/05_geographic_candidates/survey_control_point_candidates.csv",
        "data/novegeo/nngla/geometry-roads-addresses/source/05_geographic_candidates/survey_control_point_candidates_v002.csv",
        "geography.nngla_survey_control_point",
        frozenset({
            "survey_control_candidate_id", "source_point_id", "candidate_role", "longitude",
            "latitude", "crs_code", "accuracy_class_code", "qualification_status",
            "survey_id", "observed_at", "runtime_effect_scope", "source_reference",
        }),
    ),
)


def _read_header_and_count(path: Path) -> tuple[frozenset[str], int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        header = frozenset(reader.fieldnames or ())
        count = sum(1 for _ in reader)
    return header, count


def _relation_exists(connection, relation: str) -> bool:
    with connection.cursor() as cur:
        cur.execute("SELECT to_regclass(%s) IS NOT NULL", (relation,))
        return bool(cur.fetchone()[0])


def assess_empty_registers(root: Path, connection=None) -> tuple[EmptyRegisterStatus, ...]:
    statuses: list[EmptyRegisterStatus] = []
    for contract in EMPTY_REGISTER_CONTRACTS:
        historical = root / contract.historical_path
        operational = root / contract.operational_path
        findings: list[str] = []
        historical_exists = historical.is_file()
        operational_exists = operational.is_file()
        historical_count = -1
        operational_count = -1
        operational_header: frozenset[str] = frozenset()

        if not historical_exists:
            findings.append("HISTORICAL_V001_MISSING")
        else:
            _, historical_count = _read_header_and_count(historical)
            if historical_count != 0:
                findings.append("HISTORICAL_V001_NOT_EMPTY")

        if not operational_exists:
            findings.append("OPERATIONAL_V002_MISSING")
        else:
            operational_header, operational_count = _read_header_and_count(operational)
            if operational_count != 0:
                findings.append("OPERATIONAL_V002_NOT_EMPTY")

        operational_contract_valid = contract.required_operational_fields.issubset(operational_header)
        if operational_exists and not operational_contract_valid:
            findings.append("OPERATIONAL_V002_REQUIRED_FIELDS_MISSING")

        target_relation_exists: bool | None = None
        if connection is not None:
            target_relation_exists = _relation_exists(connection, contract.target_relation)
            if not target_relation_exists:
                findings.append("TARGET_RELATION_MISSING")

        ready = (
            historical_exists
            and operational_exists
            and historical_count == 0
            and operational_count == 0
            and operational_contract_valid
            and target_relation_exists is not False
            and not findings
        )
        statuses.append(
            EmptyRegisterStatus(
                domain_key=contract.domain_key,
                historical_path=contract.historical_path,
                operational_path=contract.operational_path,
                target_relation=contract.target_relation,
                historical_exists=historical_exists,
                operational_exists=operational_exists,
                historical_row_count=historical_count,
                operational_row_count=operational_count,
                operational_contract_valid=operational_contract_valid,
                target_relation_exists=target_relation_exists,
                ready=ready,
                findings=tuple(findings),
            )
        )
    return tuple(statuses)


def empty_registers_ready(statuses: tuple[EmptyRegisterStatus, ...]) -> bool:
    return len(statuses) == len(EMPTY_REGISTER_CONTRACTS) and all(status.ready for status in statuses)


__all__ = [
    "EmptyRegisterContract",
    "EMPTY_REGISTER_CONTRACTS",
    "assess_empty_registers",
    "empty_registers_ready",
]
