"""Bundle 17G adapter from parcel-lineage candidates to the locked P006.7.7 lineage contract."""
from __future__ import annotations
from datetime import date
from registries.nngla.parcel_lineage import ParcelLineageRecord
from .contracts import ParcelLineageCandidate


def promote_lineage_candidate(candidate: ParcelLineageCandidate) -> ParcelLineageRecord:
    return ParcelLineageRecord(
        lineage_id=candidate.lineage_candidate_id.replace("parcel-lineage-candidate:", "parcel-lineage:", 1),
        action=candidate.action, predecessor_parcel_ids=candidate.predecessor_parcel_ids,
        successor_parcel_ids=candidate.successor_parcel_ids, effective_on=date.fromisoformat(candidate.effective_on),
        source_reference=candidate.source_reference,
    )


__all__ = ["promote_lineage_candidate"]
