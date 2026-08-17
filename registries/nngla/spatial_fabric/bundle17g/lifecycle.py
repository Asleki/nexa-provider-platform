"""Bundle 17G parcel recognition lifecycle before and after canonical parcel existence."""
from __future__ import annotations
from .contracts import ParcelLifecycleStage

_TRANSITIONS = {
    ParcelLifecycleStage.PHYSICAL_GROUND: ParcelLifecycleStage.PARCEL_CANDIDATE,
    ParcelLifecycleStage.PARCEL_CANDIDATE: ParcelLifecycleStage.REFERENCE_RESERVED,
    ParcelLifecycleStage.REFERENCE_RESERVED: ParcelLifecycleStage.SURVEYED,
    ParcelLifecycleStage.SURVEYED: ParcelLifecycleStage.QUALIFIED,
    ParcelLifecycleStage.QUALIFIED: ParcelLifecycleStage.RECOGNIZED,
    ParcelLifecycleStage.RECOGNIZED: ParcelLifecycleStage.REGISTERED,
}


def parcel_lifecycle_rows() -> tuple[dict[str, str], ...]:
    semantics = {
        ParcelLifecycleStage.PHYSICAL_GROUND: ("false", "false", "Physical land exists independently of any cadastral parcel."),
        ParcelLifecycleStage.PARCEL_CANDIDATE: ("false", "false", "Candidate identity only; no sovereign parcel reference exists."),
        ParcelLifecycleStage.REFERENCE_RESERVED: ("false", "true", "Sovereign parcel reference reserved but no canonical parcel exists."),
        ParcelLifecycleStage.SURVEYED: ("false", "true", "Candidate has survey evidence; registration remains deferred."),
        ParcelLifecycleStage.QUALIFIED: ("false", "true", "Candidate passes parcel qualification; recognition remains separate."),
        ParcelLifecycleStage.RECOGNIZED: ("false", "true", "Authority recognizes cadastral object; canonical register insertion is next."),
        ParcelLifecycleStage.REGISTERED: ("true", "true", "Canonical parcel record exists in the parcel register."),
    }
    rows = []
    stages = tuple(ParcelLifecycleStage)
    for index, stage in enumerate(stages, start=1):
        canonical_exists, parcel_id_required, description = semantics[stage]
        next_stage = _TRANSITIONS.get(stage)
        rows.append({
            "lifecycle_status_code": stage.value,
            "sequence": str(index),
            "canonical_parcel_exists": canonical_exists,
            "parcel_reference_required": parcel_id_required,
            "next_status_code": next_stage.value if next_stage else "",
            "status": "ACTIVE",
            "description": description,
        })
    return tuple(rows)


def advance_stage(current: ParcelLifecycleStage, target: ParcelLifecycleStage) -> ParcelLifecycleStage:
    expected = _TRANSITIONS.get(current)
    if expected is not target:
        raise ValueError(f"invalid parcel lifecycle transition {current.value} -> {target.value}")
    return target


__all__ = ["parcel_lifecycle_rows", "advance_stage"]
