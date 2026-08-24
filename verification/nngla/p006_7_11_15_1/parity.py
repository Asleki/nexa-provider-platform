"""Read-only Bundle 22B qualification against live PostgreSQL authority.

P006.7.11.15.1 verifies the already-established PostgreSQL foundation and
reports later national-map realization as progress.  Canonical identity and
foundation integrity are gates; zero place/admin/road realization is a valid
pre-construction state and must never be treated as a repair trigger.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

EXPECTED_LIVE_BASELINE = {
    "foundationMigrationCount": 18,
    "canonical": {"PLACE": 700, "ADMINISTRATIVE_AREA": 192, "ROAD": 350, "GEOGRAPHIC_FEATURE": 21},
    "spatialReferencePoints": 2411,
    "featurePublicationCandidates": 20,
    "sovereignMainlandSpecialCases": 1,
    "laterCapabilities": {
        "m006_07_11_nngla_road_network_construction": "ROAD_NETWORK_TOPOLOGY",
        "m006_07_11_nngla_governed_spatial_publication": "DURABLE_NNGLA_PUBLICATION_LEDGER",
    },
}


@dataclass(frozen=True, slots=True)
class Finding:
    gate: str
    code: str
    expected: object
    actual: object

    def as_dict(self) -> dict[str, object]:
        return {"gate": self.gate, "code": self.code, "expected": self.expected, "actual": self.actual}


def _semantic_checksum(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return sha256(encoded).hexdigest()


class Bundle22BParityVerifier:
    """Verify immutable foundation truth and observe national-map progress read-only."""

    def __init__(self, pool: Any, *, repository_root: str | Path, runtime_mode: str = "simulation") -> None:
        if pool is None:
            raise TypeError("pool is required")
        self.pool = pool
        self.repository_root = Path(repository_root)
        self.runtime_mode = str(runtime_mode).strip().lower()
        if self.runtime_mode not in {"simulation", "production"}:
            raise ValueError("runtime_mode must be simulation or production")

    def _manifest(self) -> dict[str, object]:
        path = self.repository_root / "database" / "migrations" / "migration_manifest.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        migrations = payload.get("migrations")
        if not isinstance(migrations, list) or not migrations:
            raise ValueError("migration manifest is empty or malformed")
        return payload

    @staticmethod
    def _fetchall(connection: Any, sql: str, params: tuple[object, ...] = ()) -> list[tuple[object, ...]]:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return list(cursor.fetchall())

    @staticmethod
    def _fetchone(connection: Any, sql: str, params: tuple[object, ...] = ()) -> tuple[object, ...] | None:
        with connection.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchone()

    def _relation_exists(self, connection: Any, relation: str) -> bool:
        row = self._fetchone(connection, "SELECT to_regclass(%s) IS NOT NULL", (relation,))
        return bool(row and row[0])

    def _count_if_relation(
        self,
        connection: Any,
        *,
        relation: str,
        sql: str,
        params: tuple[object, ...] = (),
    ) -> int | None:
        if not self._relation_exists(connection, relation):
            return None
        row = self._fetchone(connection, sql, params)
        return int(row[0]) if row else 0

    def qualify(self, *, repository_revision: str = "unknown") -> dict[str, object]:
        manifest = self._manifest()
        manifest_rows = sorted(manifest["migrations"], key=lambda item: int(item["sequence_number"]))
        manifest_by_id = {str(item["migration_id"]): item for item in manifest_rows}
        foundation_rows = [row for row in manifest_rows if int(row["sequence_number"]) <= EXPECTED_LIVE_BASELINE["foundationMigrationCount"]]
        later_rows = [row for row in manifest_rows if int(row["sequence_number"]) > EXPECTED_LIVE_BASELINE["foundationMigrationCount"]]
        findings: list[Finding] = []

        with self.pool.connection(read_only=True) as connection:
            db_name_row = self._fetchone(connection, "SELECT current_database()")
            ledger_available = self._relation_exists(connection, "platform.schema_migration")
            if ledger_available:
                ledger = self._fetchall(connection, """
                    SELECT migration_id, sequence_number, checksum_sha256, status
                    FROM platform.schema_migration
                    ORDER BY sequence_number, migration_id
                """)
            else:
                ledger = []
                findings.append(Finding("foundationSchema", "MISSING_MIGRATION_LEDGER", True, "platform.schema_migration"))

            ledger_by_id = {
                str(mid): {"sequence": int(seq), "checksum": str(checksum), "status": str(status)}
                for mid, seq, checksum, status in ledger
            }
            foundation_ids = [str(row["migration_id"]) for row in foundation_rows]
            later_ids = [str(row["migration_id"]) for row in later_rows]
            unknown_ids = sorted(set(ledger_by_id) - set(manifest_by_id))
            failed_ids = sorted(mid for mid, row in ledger_by_id.items() if row["status"] == "FAILED")
            started_ids = sorted(mid for mid, row in ledger_by_id.items() if row["status"] == "STARTED")
            missing_foundation = sorted(mid for mid in foundation_ids if ledger_by_id.get(mid, {}).get("status") != "APPLIED")
            applied_known = [mid for mid in manifest_by_id if ledger_by_id.get(mid, {}).get("status") == "APPLIED"]
            checksum_drift = sorted(
                mid for mid in applied_known
                if ledger_by_id[mid]["checksum"] != str(manifest_by_id[mid]["forward_sha256"])
            )
            sequence_drift = sorted(
                mid for mid in applied_known
                if ledger_by_id[mid]["sequence"] != int(manifest_by_id[mid]["sequence_number"])
            )

            if len(foundation_rows) != EXPECTED_LIVE_BASELINE["foundationMigrationCount"]:
                findings.append(Finding("foundationSchema", "FOUNDATION_MANIFEST_COUNT", EXPECTED_LIVE_BASELINE["foundationMigrationCount"], len(foundation_rows)))
            if missing_foundation:
                findings.append(Finding("foundationSchema", "FOUNDATION_MIGRATIONS_NOT_APPLIED", [], missing_foundation))
            if failed_ids:
                findings.append(Finding("foundationSchema", "FAILED_MIGRATIONS", [], failed_ids))
            if started_ids:
                findings.append(Finding("foundationSchema", "STARTED_MIGRATIONS", [], started_ids))
            if checksum_drift:
                findings.append(Finding("foundationSchema", "CHECKSUM_DRIFT", [], checksum_drift))
            if sequence_drift:
                findings.append(Finding("foundationSchema", "SEQUENCE_DRIFT", [], sequence_drift))
            if unknown_ids:
                findings.append(Finding("foundationSchema", "UNKNOWN_DATABASE_MIGRATIONS", [], unknown_ids))

            later_capabilities: dict[str, object] = {}
            for migration in later_rows:
                migration_id = str(migration["migration_id"])
                ledger_row = ledger_by_id.get(migration_id)
                applied = bool(ledger_row and ledger_row["status"] == "APPLIED")
                objects: dict[str, bool] = {}
                expected_objects = migration.get("expected_objects", {})
                for table in expected_objects.get("tables", []):
                    objects[str(table)] = self._relation_exists(connection, str(table))
                for index in expected_objects.get("indexes", []):
                    schema, index_name = str(index).split(".", 1) if "." in str(index) else ("geography", str(index))
                    row = self._fetchone(
                        connection,
                        "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE schemaname=%s AND indexname=%s)",
                        (schema, index_name),
                    )
                    objects[str(index)] = bool(row and row[0])
                if applied and not all(objects.values()):
                    findings.append(Finding("laterCapabilityIntegrity", "APPLIED_CAPABILITY_OBJECT_MISSING", True, {migration_id: [name for name, present in objects.items() if not present]}))
                later_capabilities[migration_id] = {
                    "sequenceNumber": int(migration["sequence_number"]),
                    "capability": EXPECTED_LIVE_BASELINE["laterCapabilities"].get(migration_id, "LATER_ADDITIVE_CAPABILITY"),
                    "ledgerStatus": ledger_row["status"] if ledger_row else "NOT_APPLIED",
                    "installed": applied,
                    "requiredObjects": objects,
                    "state": "INSTALLED" if applied else "DEFERRED_NOT_INSTALLED",
                }

            canonical_queries = {
                "PLACE": ("geography.nngla_place_reference", "SELECT COUNT(*)::bigint FROM geography.nngla_place_reference"),
                "ADMINISTRATIVE_AREA": ("geography.nngla_administrative_area", "SELECT COUNT(*)::bigint FROM geography.nngla_administrative_area"),
                "ROAD": ("geography.nngla_road", "SELECT COUNT(*)::bigint FROM geography.nngla_road"),
                "GEOGRAPHIC_FEATURE": (
                    "geography.nngla_canonical_crosswalk",
                    "SELECT COUNT(*)::bigint FROM geography.nngla_canonical_crosswalk WHERE dataset_id='dataset:novegeo:geographic-features:v001:21' AND dataset_version='1'",
                ),
            }
            canonical: dict[str, int | None] = {}
            for family, (relation, sql) in canonical_queries.items():
                canonical[family] = self._count_if_relation(connection, relation=relation, sql=sql)
                expected = EXPECTED_LIVE_BASELINE["canonical"][family]
                if canonical[family] != expected:
                    findings.append(Finding("canonicalFoundation", family, expected, canonical[family] if canonical[family] is not None else "RELATION_UNAVAILABLE"))

            spatial_reference_authority = self._count_if_relation(
                connection,
                relation="geography.nngla_geometry_authority_record",
                sql="SELECT COUNT(*)::bigint FROM geography.nngla_geometry_authority_record WHERE geometry_role_code='SPATIAL_REFERENCE_POINT' AND valid_to IS NULL",
            )
            spatial_reference_versions = self._count_if_relation(
                connection,
                relation="geography.nngla_geometry_version",
                sql="SELECT COUNT(*)::bigint FROM geography.nngla_geometry_version WHERE geometry_role_code='SPATIAL_REFERENCE_POINT' AND valid_to IS NULL",
            )
            for code, value in (("SPATIAL_REFERENCE_POINT_AUTHORITY", spatial_reference_authority), ("SPATIAL_REFERENCE_POINT_VERSION", spatial_reference_versions)):
                if value != EXPECTED_LIVE_BASELINE["spatialReferencePoints"]:
                    findings.append(Finding("coordinateFoundation", code, EXPECTED_LIVE_BASELINE["spatialReferencePoints"], value if value is not None else "RELATION_UNAVAILABLE"))

            role_counts: dict[str, int | None] = {}
            for role in ("PLACE_REFERENCE_POINT", "SETTLEMENT_FOOTPRINT", "ADMINISTRATIVE_BOUNDARY", "ROAD_ALIGNMENT"):
                role_counts[role] = self._count_if_relation(
                    connection,
                    relation="geography.nngla_geometry_authority_record",
                    sql="SELECT COUNT(*)::bigint FROM geography.nngla_geometry_authority_record WHERE geometry_role_code=%s AND valid_to IS NULL",
                    params=(role,),
                )

            assignment_queries = {
                "placesSpatiallyAssociated": ("geography.nngla_place_reference", "SELECT COUNT(*)::bigint FROM geography.nngla_place_reference WHERE geometry_reference IS NOT NULL"),
                "administrativeBoundariesAssociated": ("geography.nngla_administrative_area", "SELECT COUNT(*)::bigint FROM geography.nngla_administrative_area WHERE geometry_reference IS NOT NULL"),
                "roadsGeometryAssociated": ("geography.nngla_road", "SELECT COUNT(*)::bigint FROM geography.nngla_road WHERE geometry_id IS NOT NULL"),
                "addressesIssued": ("geography.nngla_address", "SELECT COUNT(*)::bigint FROM geography.nngla_address"),
            }
            assignments = {
                key: self._count_if_relation(connection, relation=relation, sql=sql)
                for key, (relation, sql) in assignment_queries.items()
            }

            topology_relations = {
                "segments": "geography.nngla_road_segment_topology",
                "nodes": "geography.nngla_road_network_node",
                "connections": "geography.nngla_road_network_connection",
                "relationships": "geography.nngla_spatial_relationship_evidence",
            }
            topology_available = all(self._relation_exists(connection, relation) for relation in topology_relations.values())
            if topology_available:
                topology = {
                    "segments": self._count_if_relation(connection, relation=topology_relations["segments"], sql="SELECT COUNT(*)::bigint FROM geography.nngla_road_segment_topology"),
                    "nodes": self._count_if_relation(connection, relation=topology_relations["nodes"], sql="SELECT COUNT(*)::bigint FROM geography.nngla_road_network_node"),
                    "junctionNodes": self._count_if_relation(connection, relation=topology_relations["nodes"], sql="SELECT COUNT(*)::bigint FROM geography.nngla_road_network_node WHERE node_role='JUNCTION'"),
                    "connections": self._count_if_relation(connection, relation=topology_relations["connections"], sql="SELECT COUNT(*)::bigint FROM geography.nngla_road_network_connection"),
                    "relationships": self._count_if_relation(connection, relation=topology_relations["relationships"], sql="SELECT COUNT(*)::bigint FROM geography.nngla_spatial_relationship_evidence"),
                }
            else:
                topology = {"segments": None, "nodes": None, "junctionNodes": None, "connections": None, "relationships": None}

            if self._relation_exists(connection, "geography.nngla_spatial_read_projection_v1"):
                projection_row = self._fetchone(connection, """
                    SELECT
                      COUNT(*)::bigint,
                      COUNT(*) FILTER (WHERE geometry_id IS NOT NULL)::bigint
                    FROM geography.nngla_spatial_read_projection_v1
                    WHERE runtime_mode=%s AND visibility='PUBLIC'
                """, (self.runtime_mode,)) or (0, 0)
                public_projection = int(projection_row[0])
                map_renderable = int(projection_row[1])
            else:
                public_projection = None
                map_renderable = None
                findings.append(Finding("publicReadFoundation", "READ_PROJECTION_RELATION", True, "RELATION_UNAVAILABLE"))

            publication_ledger_available = self._relation_exists(connection, "geography.nngla_publication_record")
            if publication_ledger_available:
                publication_row = self._fetchone(connection, "SELECT COUNT(*)::bigint FROM geography.nngla_publication_record") or (0,)
                durable_publication_records: int | None = int(publication_row[0])
            else:
                durable_publication_records = None

        feature_reconciliation = {
            "canonicalGeographicFeatures": canonical["GEOGRAPHIC_FEATURE"],
            "genericPublicationCandidates": EXPECTED_LIVE_BASELINE["featurePublicationCandidates"],
            "sovereignMainlandSpecialCases": EXPECTED_LIVE_BASELINE["sovereignMainlandSpecialCases"],
            "differenceExplained": isinstance(canonical["GEOGRAPHIC_FEATURE"], int)
            and canonical["GEOGRAPHIC_FEATURE"] == (
                EXPECTED_LIVE_BASELINE["featurePublicationCandidates"] + EXPECTED_LIVE_BASELINE["sovereignMainlandSpecialCases"]
            ),
        }
        if not feature_reconciliation["differenceExplained"]:
            findings.append(Finding("canonicalFoundation", "FEATURE_21_20_1_RECONCILIATION", True, False))

        def remaining(total: int, value: int | None) -> int | None:
            return None if value is None else max(0, total - value)

        report = {
            "qualificationSchema": "npp.nngla.bundle22b-readiness",
            "qualificationSchemaVersion": 2,
            "milestone": "P006.7.11.15.1",
            "repositoryRevision": repository_revision,
            "databaseName": str(db_name_row[0]) if db_name_row else "unknown",
            "runtimeMode": self.runtime_mode,
            "foundationSchema": {
                "repositoryMigrationCount": len(manifest_rows),
                "foundationExpectedCount": EXPECTED_LIVE_BASELINE["foundationMigrationCount"],
                "foundationAppliedCount": sum(1 for mid in foundation_ids if ledger_by_id.get(mid, {}).get("status") == "APPLIED"),
                "ledgerRecordCount": len(ledger),
                "failedCount": len(failed_ids),
                "startedCount": len(started_ids),
                "checksumDriftCount": len(checksum_drift),
                "sequenceDriftCount": len(sequence_drift),
                "unknownDatabaseMigrationCount": len(unknown_ids),
            },
            "laterCapabilities": later_capabilities,
            "canonicalFoundation": canonical,
            "coordinateFoundation": {
                "expected": EXPECTED_LIVE_BASELINE["spatialReferencePoints"],
                "authorityRecords": spatial_reference_authority,
                "geometryVersions": spatial_reference_versions,
            },
            "realizationState": {
                "places": {
                    "canonical": canonical["PLACE"],
                    "spatiallyAssociated": assignments["placesSpatiallyAssociated"],
                    "remaining": remaining(EXPECTED_LIVE_BASELINE["canonical"]["PLACE"], assignments["placesSpatiallyAssociated"]),
                },
                "administrativeAreas": {
                    "canonical": canonical["ADMINISTRATIVE_AREA"],
                    "boundariesAssociated": assignments["administrativeBoundariesAssociated"],
                    "remaining": remaining(EXPECTED_LIVE_BASELINE["canonical"]["ADMINISTRATIVE_AREA"], assignments["administrativeBoundariesAssociated"]),
                },
                "roads": {
                    "canonical": canonical["ROAD"],
                    "geometryAssociated": assignments["roadsGeometryAssociated"],
                    "remaining": remaining(EXPECTED_LIVE_BASELINE["canonical"]["ROAD"], assignments["roadsGeometryAssociated"]),
                },
                "addressesIssued": assignments["addressesIssued"],
                "geometryRoles": role_counts,
                "roadTopology": {"schemaAvailable": topology_available, "counts": topology},
            },
            "featureParity": feature_reconciliation,
            "publicReadState": {
                "publicProjection": public_projection,
                "mapRenderable": map_renderable,
                "durablePublicationLedgerAvailable": publication_ledger_available,
                "durablePublicationRecords": durable_publication_records,
            },
            "findings": [finding.as_dict() for finding in findings],
        }
        report["overallStatus"] = "PASS" if not findings else "FAIL"
        report["semanticChecksum"] = _semantic_checksum(report)
        return report


__all__ = ["Bundle22BParityVerifier", "EXPECTED_LIVE_BASELINE", "Finding"]
