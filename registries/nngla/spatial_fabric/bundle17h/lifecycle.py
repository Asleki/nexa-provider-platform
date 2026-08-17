"""Bundle 17H site lifecycle vocabulary; construction lifecycle remains external."""
from __future__ import annotations

from .contracts import SiteLifecycleStage

_TRANSITIONS = {
    SiteLifecycleStage.CANDIDATE: SiteLifecycleStage.SPATIALLY_QUALIFIED,
    SiteLifecycleStage.SPATIALLY_QUALIFIED: SiteLifecycleStage.ADDRESS_ELIGIBLE,
    SiteLifecycleStage.ADDRESS_ELIGIBLE: SiteLifecycleStage.ADDRESS_ASSIGNED,
    SiteLifecycleStage.ADDRESS_ASSIGNED: SiteLifecycleStage.ACTIVE,
    SiteLifecycleStage.ACTIVE: SiteLifecycleStage.RETIRED,
}


def site_lifecycle_rows() -> tuple[dict[str, str], ...]:
    descriptions = {
        SiteLifecycleStage.CANDIDATE: "Stable site candidate only; not yet qualified and not a building or residence.",
        SiteLifecycleStage.SPATIALLY_QUALIFIED: "Site passes NNGLA spatial qualification; construction state remains external.",
        SiteLifecycleStage.ADDRESS_ELIGIBLE: "Site may receive an address under a governed address series.",
        SiteLifecycleStage.ADDRESS_ASSIGNED: "Governed address has been assigned; site and address identities remain distinct.",
        SiteLifecycleStage.ACTIVE: "Addressable site is active for cross-registry reference.",
        SiteLifecycleStage.RETIRED: "Historical site identity retained but no longer active.",
    }
    rows = []
    for index, stage in enumerate(SiteLifecycleStage, start=1):
        rows.append({
            "site_lifecycle_status_code": stage.value, "sequence": str(index),
            "canonical_site_exists": "true" if stage in {SiteLifecycleStage.ADDRESS_ASSIGNED, SiteLifecycleStage.ACTIVE, SiteLifecycleStage.RETIRED} else "false",
            "address_required": "true" if stage in {SiteLifecycleStage.ADDRESS_ASSIGNED, SiteLifecycleStage.ACTIVE} else "false",
            "construction_state_owned_by_nngla": "false", "citizen_residence_owned_by_nngla": "false",
            "next_status_code": _TRANSITIONS.get(stage).value if stage in _TRANSITIONS else "",
            "status": "ACTIVE", "description": descriptions[stage],
        })
    return tuple(rows)


def structure_reference_type_rows() -> tuple[dict[str, str], ...]:
    types = (
        ("HOUSE", "House / dwelling structure"), ("SCHOOL_BUILDING", "School or education building"),
        ("HEALTH_FACILITY", "Hospital, clinic or health facility"), ("SHOP", "Retail or service premises"),
        ("WAREHOUSE", "Warehouse or storage structure"), ("FACTORY", "Manufacturing structure"),
        ("UTILITY_STRUCTURE", "Utility/infrastructure structure"), ("PUBLIC_BUILDING", "Public institutional building"),
        ("OTHER_GOVERNED", "Other externally governed structure type"),
    )
    return tuple({
        "structure_reference_type_code": code, "canonical_label": label,
        "nngla_owns_structure_record": "false", "external_reference_required": "true",
        "status": "ACTIVE", "description": "Typed NNGLA relationship to an externally owned structure record.",
    } for code, label in types)


def advance_site_stage(current: SiteLifecycleStage, target: SiteLifecycleStage) -> SiteLifecycleStage:
    if _TRANSITIONS.get(current) is not target:
        raise ValueError(f"invalid site lifecycle transition {current.value} -> {target.value}")
    return target


__all__ = ["site_lifecycle_rows", "structure_reference_type_rows", "advance_site_stage"]
