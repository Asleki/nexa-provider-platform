"""Bundle 17I title legal lifecycle; number reservation remains distinct from issuance."""
from __future__ import annotations
from .contracts import TitleLifecycleStage

_TRANSITIONS = {
    TitleLifecycleStage.TITLE_NUMBER_RESERVED: TitleLifecycleStage.ISSUANCE_CANDIDATE,
    TitleLifecycleStage.ISSUANCE_CANDIDATE: TitleLifecycleStage.TITLE_ISSUED,
    TitleLifecycleStage.TITLE_ISSUED: TitleLifecycleStage.ACTIVE,
    TitleLifecycleStage.ACTIVE: TitleLifecycleStage.SUSPENDED,
    TitleLifecycleStage.SUSPENDED: TitleLifecycleStage.ACTIVE,
}


def title_lifecycle_rows() -> tuple[dict[str, str], ...]:
    legal_exists = {
        TitleLifecycleStage.TITLE_NUMBER_RESERVED: False,
        TitleLifecycleStage.ISSUANCE_CANDIDATE: False,
        TitleLifecycleStage.TITLE_ISSUED: True,
        TitleLifecycleStage.ACTIVE: True,
        TitleLifecycleStage.SUSPENDED: True,
        TitleLifecycleStage.CANCELLED: True,
        TitleLifecycleStage.EXPIRED: True,
        TitleLifecycleStage.REPLACED: True,
        TitleLifecycleStage.HISTORICAL: True,
    }
    descriptions = {
        TitleLifecycleStage.TITLE_NUMBER_RESERVED: "Identifier reserved only; parcel and holder may be absent and no legal title exists.",
        TitleLifecycleStage.ISSUANCE_CANDIDATE: "Reservation linked to proposed parcel, title type, tenure and holder; legal issuance pending.",
        TitleLifecycleStage.TITLE_ISSUED: "Title has been legally issued but activation/publication may be a separate workflow.",
        TitleLifecycleStage.ACTIVE: "Current active title relationship.",
        TitleLifecycleStage.SUSPENDED: "Title exists but operational/legal use is suspended subject to authority process.",
        TitleLifecycleStage.CANCELLED: "Historical title identity retained after cancellation.",
        TitleLifecycleStage.EXPIRED: "Historical title identity retained after expiry.",
        TitleLifecycleStage.REPLACED: "Historical title identity retained and linked to replacement title.",
        TitleLifecycleStage.HISTORICAL: "Retained non-current legal record.",
    }
    rows = []
    for index, stage in enumerate(TitleLifecycleStage, start=1):
        rows.append({
            "title_lifecycle_status_code": stage.value, "sequence": str(index),
            "legal_title_exists": str(legal_exists[stage]).lower(),
            "title_number_reserved": "true",
            "parcel_required": "false" if stage is TitleLifecycleStage.TITLE_NUMBER_RESERVED else "true",
            "holder_reference_required": "false" if stage is TitleLifecycleStage.TITLE_NUMBER_RESERVED else "true",
            "status": "ACTIVE", "description": descriptions[stage],
        })
    return tuple(rows)


__all__ = ["title_lifecycle_rows"]
