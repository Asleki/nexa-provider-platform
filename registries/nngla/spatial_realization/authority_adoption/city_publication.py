"""Production-coherent CITY publication into the existing NNGLA read projection."""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json

from registries.nngla.publication_policy15d import decide_administrative_area_visibility


class CityPublicationError(RuntimeError):
    pass


def _digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _stable_id(prefix: str, value: object) -> str:
    return prefix + _digest(value)


@dataclass(frozen=True, slots=True)
class CityPublicationReceipt:
    subject_id: str
    geometry_id: str
    publication_id: str
    publication_version: int
    projection_id: str
    read_model_version: int
    runtime_mode: str
    content_sha256: str


class PostgreSQLCityPublicationRepository:
    """Publish only the exact current qualified/legalized production CITY authority."""

    def __init__(self, connection) -> None:
        self.connection = connection

    def publish_city(self, administrative_area_id: str, *, submitted_by: str, approved_by: str) -> CityPublicationReceipt:
        if not submitted_by or not approved_by or submitted_by == approved_by:
            raise ValueError("CITY publication requires distinct submitter and approver")
        if not administrative_area_id.startswith("NG-ADM-"):
            raise ValueError("CITY publication requires NG-ADM identity")
        runtime = "production"
        try:
            with self.connection.cursor() as cur:
                cur.execute(
                    """SELECT a.administrative_type_code,a.canonical_name,a.boundary_status,a.lifecycle_status_code,a.geometry_reference,
                              g.geometry_id,g.runtime_mode,g.source_sha256,
                              ar.qualification_status,ar.publication_status,ar.runtime_effect_scope,
                              ass.assignment_id,ass.assignment_status,ass.qualification_id,
                              leg.legalization_id,leg.decision_status,q.qualification_sha256
                       FROM geography.nngla_administrative_area a
                       JOIN geography.nngla_geometry_version g
                         ON g.geometry_id=a.geometry_reference AND g.runtime_mode='production' AND g.valid_to IS NULL
                       JOIN geography.nngla_geometry_authority_record ar
                         ON ar.geometry_id=g.geometry_id AND ar.subject_id=a.administrative_area_id AND ar.valid_to IS NULL
                       JOIN geography.nngla_administrative_geometry_assignment ass
                         ON ass.administrative_area_id=a.administrative_area_id AND ass.geometry_id=g.geometry_id
                        AND ass.assignment_status='EFFECTIVE' AND ass.effective_to IS NULL
                       JOIN geography.nngla_administrative_legalization_decision leg
                         ON leg.assignment_id=ass.assignment_id AND leg.geometry_id=g.geometry_id AND leg.decision_status='LEGALIZED'
                       JOIN geography.nngla_city_feature_qualification q
                         ON q.qualification_id=ass.qualification_id AND q.feature_qualification_status='FEATURE_QUALIFIED'
                        AND q.runtime_mode='production'
                       WHERE a.administrative_area_id=%s FOR UPDATE OF a,ar""",
                    (administrative_area_id,),
                )
                row = cur.fetchone()
                if row is None:
                    raise CityPublicationError("CITY production authority chain is incomplete")
                if str(row[0]) != "CITY":
                    raise CityPublicationError("Delivery 3 publishes CITY administrative areas only")
                display_name = str(row[1])
                boundary_status = str(row[2]); lifecycle = str(row[3]); geometry_id = str(row[5])
                if str(row[6]) != runtime:
                    raise CityPublicationError("CITY geometry runtime is not production")
                if str(row[8]) != "QUALIFIED" or str(row[12]) != "EFFECTIVE" or str(row[15]) != "LEGALIZED":
                    raise CityPublicationError("CITY qualification/assignment/legalization chain is not current")
                policy = decide_administrative_area_visibility(
                    lifecycle_status=lifecycle,
                    boundary_status=boundary_status,
                    geometry_reference=geometry_id,
                    published_through_gate=True,
                )
                if not policy.public_eligible:
                    raise CityPublicationError("CITY fails existing NNGLA publication policy: " + ",".join(policy.reasons))

                cur.execute(
                    """SELECT COALESCE(MAX(publication_version),0),
                              (SELECT publication_id FROM geography.nngla_publication_record
                               WHERE subject_id=%s AND runtime_mode='production' AND decision='PUBLISHED'
                               ORDER BY publication_version DESC LIMIT 1)
                       FROM geography.nngla_publication_record
                       WHERE subject_id=%s AND runtime_mode='production'""",
                    (administrative_area_id, administrative_area_id),
                )
                pv = cur.fetchone()
                publication_version = int(pv[0]) + 1 if pv else 1
                supersedes_publication_id = str(pv[1]) if pv and pv[1] is not None else None
                cur.execute(
                    """SELECT COALESCE(MAX(read_model_version),0)
                       FROM geography.nngla_spatial_read_projection_v1
                       WHERE subject_id=%s AND runtime_mode='production'""",
                    (administrative_area_id,),
                )
                rv = cur.fetchone()
                read_model_version = int(rv[0]) + 1 if rv else 1

                material = {
                    "subjectId":administrative_area_id,"recordFamily":"ADMINISTRATIVE_AREA","runtimeMode":runtime,
                    "geometryId":geometry_id,"publicationVersion":publication_version,"readModelVersion":read_model_version,
                    "displayName":display_name,"assignmentId":str(row[11]),"legalizationId":str(row[14]),
                    "qualificationId":str(row[13]),"qualificationSha256":str(row[16]),
                }
                content_sha = _digest(material)
                publication_id = _stable_id("publication:nngla:", material)
                projection_id = _stable_id("read:nngla:", {
                    "subject":administrative_area_id,"runtime":runtime,"readModelVersion":read_model_version,"publication":publication_id,
                })

                if supersedes_publication_id:
                    cur.execute(
                        """UPDATE geography.nngla_publication_record
                           SET decision='SUPERSEDED'
                           WHERE publication_id=%s AND runtime_mode='production' AND decision='PUBLISHED'""",
                        (supersedes_publication_id,),
                    )
                cur.execute(
                    """INSERT INTO geography.nngla_publication_record(
                           publication_id,publication_version,subject_id,record_family,canonical_version,runtime_mode,visibility,
                           geometry_id,geometry_version,decision,submitted_by,approved_by,content_sha256,supersedes_publication_id)
                       VALUES(%s,%s,%s,'ADMINISTRATIVE_AREA',1,'production','PUBLIC',%s,1,'PUBLISHED',%s,%s,%s,%s)""",
                    (publication_id,publication_version,administrative_area_id,geometry_id,submitted_by,approved_by,content_sha,supersedes_publication_id),
                )
                cur.execute(
                    """INSERT INTO geography.nngla_spatial_read_projection_v1(
                           projection_id,subject_id,record_family,display_name,runtime_mode,visibility,publication_reference,
                           geometry_id,geometry_version,read_model_version)
                       VALUES(%s,%s,'ADMINISTRATIVE_AREA',%s,'production','PUBLIC',%s,%s,1,%s)""",
                    (projection_id,administrative_area_id,display_name,publication_id,geometry_id,read_model_version),
                )
                cur.execute(
                    """UPDATE geography.nngla_geometry_authority_record SET publication_status='PUBLISHED'
                       WHERE geometry_id=%s AND subject_id=%s AND qualification_status='QUALIFIED' AND valid_to IS NULL""",
                    (geometry_id,administrative_area_id),
                )
                if getattr(cur,"rowcount",1) != 1:
                    raise CityPublicationError("qualified CITY authority publication state update failed")
                cur.execute(
                    """SELECT p.publication_reference,p.geometry_id,p.read_model_version,g.runtime_mode
                       FROM geography.nngla_spatial_read_projection_v1 p
                       JOIN geography.nngla_geometry_version g ON g.geometry_id=p.geometry_id AND g.valid_to IS NULL
                       WHERE p.projection_id=%s AND p.visibility='PUBLIC' AND p.runtime_mode='production'""",
                    (projection_id,),
                )
                rb = cur.fetchone()
                if rb is None or str(rb[0]) != publication_id or str(rb[1]) != geometry_id or int(rb[2]) != read_model_version or str(rb[3]) != "production":
                    raise CityPublicationError("production CITY publication readback mismatch")
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
        return CityPublicationReceipt(
            subject_id=administrative_area_id,
            geometry_id=geometry_id,
            publication_id=publication_id,
            publication_version=publication_version,
            projection_id=projection_id,
            read_model_version=read_model_version,
            runtime_mode=runtime,
            content_sha256=content_sha,
        )


__all__ = ["CityPublicationError","CityPublicationReceipt","PostgreSQLCityPublicationRepository"]
