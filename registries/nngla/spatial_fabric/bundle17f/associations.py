"""Bundle 17F association candidates around existing canonical identities."""
from __future__ import annotations
from functools import lru_cache

from .canonical_alignment import derive_existing_canonical_alignment
from .contracts import AssociationStatus, CanonicalSubjectFamily, SubjectSpatialAssociationCandidate


@lru_cache(maxsize=1)
def derive_subject_spatial_association_candidates() -> tuple[SubjectSpatialAssociationCandidate, ...]:
    out = []
    for alignment in derive_existing_canonical_alignment():
        if alignment.object_family is CanonicalSubjectFamily.EXISTING_GEOMETRY:
            continue
        if alignment.geometry_status == "DIRECT_EXISTING_GEOMETRY_SUBJECT_MATCH":
            status = AssociationStatus.READY_ASSOCIATE_EXISTING_GEOMETRY
            basis = "DIRECT_SOURCE_SUBJECT_TO_EXISTING_GEOMETRY_SUBJECT_MATCH"
            geometry_role = "EXISTING_GOVERNED_FEATURE_GEOMETRY"
            source_geometry_subject = alignment.source_record_id
        elif alignment.geometry_status == "RELATED_SOVEREIGN_GEOMETRY_NOT_DIRECT_SUBJECT_MATCH":
            status = AssociationStatus.SUBJECT_ROLE_RECONCILIATION_REQUIRED
            basis = "RELATED_GEOMETRY_EXISTS_BUT_COUNTRY_AND_MAINLAND_SUBJECTS_ARE_DISTINCT"
            geometry_role = "RELATED_SOVEREIGN_BOUNDARY_NOT_ASSIGNED"
            source_geometry_subject = "country:novegeo"
        else:
            status = AssociationStatus.DEFERRED_NO_GEOMETRY
            basis = "CANONICAL_IDENTITY_CONFIRMED_BUT_NO_GOVERNED_ASSOCIABLE_GEOMETRY_EXISTS"
            geometry_role = ""
            source_geometry_subject = ""
        out.append(SubjectSpatialAssociationCandidate(
            association_candidate_id=f"assocand:nngla:{alignment.object_family.value.lower()}:{alignment.canonical_id}",
            subject_family=alignment.object_family,
            canonical_subject_id=alignment.canonical_id,
            source_subject_id=alignment.source_record_id,
            geometry_id=alignment.geometry_id if status is AssociationStatus.READY_ASSOCIATE_EXISTING_GEOMETRY else "",
            geometry_role_code=geometry_role,
            source_geometry_subject_id=source_geometry_subject,
            association_status=status,
            association_basis=basis,
            runtime_effect_scope="SHARED_REFERENCE",
            notes=alignment.notes,
        ))
    return tuple(out)


__all__ = ["derive_subject_spatial_association_candidates"]
