from infrastructure.api.services.nngla_postgresql_read_service import PostgreSQLNNGLAReadService
from infrastructure.database.read.nngla import NNGLAFamilyCounts


class StubRepository:
    runtime_mode = "simulation"

    def family_counts(self):
        return {
            "PLACE": NNGLAFamilyCounts(700, 700, 0, 0),
            "ADMINISTRATIVE_AREA": NNGLAFamilyCounts(192, 192, 0, 0),
            "GEOGRAPHIC_FEATURE": NNGLAFamilyCounts(21, 21, 0, 0),
            "ROAD": NNGLAFamilyCounts(900, 350, 0, 0),
            "ADDRESS": NNGLAFamilyCounts(0, 0, 0, 0),
            "PARCEL": NNGLAFamilyCounts(0, 0, 0, 0),
        }

    def read_model_version(self):
        return 1

    def coordinate_migration_status(self):
        return "EXECUTED"

    def public_items(self, family):
        return ()


def test_live_nngla_status_reports_postgresql_canonical_truth_without_publishing_internal_spatial_points():
    body = PostgreSQLNNGLAReadService(StubRepository()).status_dict()
    families = {item["family"]: item for item in body["families"]}

    assert body["databaseAuthority"] == "SERVER_SIDE_ONLY"
    assert body["liveDatabaseMigrationStatus"] == "EXECUTED"
    assert body["readRuntime"] == "simulation"
    assert families["PLACE"]["canonicalCount"] == 700
    assert families["ADMINISTRATIVE_AREA"]["canonicalCount"] == 192
    assert families["ROAD"]["sourceCount"] == 900
    assert families["ROAD"]["canonicalCount"] == 350
    assert families["GEOGRAPHIC_FEATURE"]["canonicalCount"] == 21
    assert sum(item["canonicalCount"] for item in body["families"]) == 1263
    assert all(item["publishedCount"] == 0 and item["mapRenderableCount"] == 0 for item in body["families"])


def test_live_nngla_public_family_uses_projection_only_and_remains_empty_before_publication():
    body = PostgreSQLNNGLAReadService(StubRepository()).list_public("PLACE")
    assert body["family"] == "PLACE"
    assert body["items"] == []
    assert body["count"] == 0
    assert body["canonicalCount"] == 700
    assert body["publishedCount"] == 0
    assert body["mapRenderableCount"] == 0
