"""Read-only PostgreSQL target inspection for NNGLA migration previews."""
from __future__ import annotations
from .preview import TargetStateSnapshot

_CAPABILITY_TABLES = {
    "world_geometry_authority": "geography.world_boundary",
    "nngla_execution_foundation": "geography.nngla_canonical_crosswalk",
    "nngla_geographic_identity_places": "geography.nngla_place_reference",
    "nngla_geometry_roads_addresses": "geography.nngla_road",
    "nngla_cadastre_titles_state_land": "geography.nngla_parcel",
}

class PostgreSQLTargetInspector:
    def __init__(self, connection): self.connection = connection
    def snapshot(self, database_name: str, environment_name: str) -> TargetStateSnapshot:
        capabilities: set[str] = set()
        with self.connection.cursor() as cur:
            for capability, relation in _CAPABILITY_TABLES.items():
                cur.execute("SELECT to_regclass(%s) IS NOT NULL", (relation,))
                if bool(cur.fetchone()[0]): capabilities.add(capability)
            occupied: set[str] = set()
            for relation, column in (
                ("geography.nngla_place_reference", "place_id"),
                ("geography.nngla_administrative_area", "administrative_area_id"),
                ("geography.nngla_road", "road_id"),
                ("geography.nngla_spatial_feature", "feature_id"),
                ("geography.nngla_geometry_authority_record", "geometry_id"),
                ("geography.nngla_address", "address_id"),
                ("geography.nngla_title", "title_id"),
            ):
                cur.execute("SELECT to_regclass(%s) IS NOT NULL", (relation,))
                if bool(cur.fetchone()[0]):
                    cur.execute(f"SELECT {column} FROM {relation}")
                    occupied.update(str(row[0]) for row in cur.fetchall())
        return TargetStateSnapshot(database_name, environment_name, frozenset(capabilities), frozenset(occupied))

__all__ = ["PostgreSQLTargetInspector"]
