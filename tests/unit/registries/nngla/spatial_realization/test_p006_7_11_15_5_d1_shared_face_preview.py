from pathlib import Path

from registries.nngla.spatial_realization.shared_face_preview import (
    build_read_only_shared_face_preview,
    preview_payload,
)


def test_delivery1_default_preview_fails_closed_at_governed_material_faces_without_writing():
    preview=build_read_only_shared_face_preview("NG-PLC-000086")
    payload=preview_payload(preview)
    assert preview.status=="GOVERNED_DECISION_REQUIRED"
    assert payload["writeCapability"]=="NONE"
    assert payload["canonicalDatabaseMutation"] is False
    assert payload["faces"]["materialDefects"]
    assert payload["assignment"] is None


def test_delivery1_preview_module_has_no_persistence_or_execution_dependency():
    body=Path("registries/nngla/spatial_realization/shared_face_preview.py").read_text()
    assert "persistence" not in body
    assert "execute_preview" not in body
    assert "reserve_geometry" not in body
    assert "persist_geometry" not in body
