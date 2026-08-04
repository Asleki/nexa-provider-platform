"""Unit tests for pwa_roadmap_data."""
import pytest

import pwa_roadmap_data as data


def test_current_canonical_summary_is_consistent() -> None:
    summary = data.roadmap_summary()
    assert summary["version"] == "0.2.0"
    assert summary["start"] == "P001"
    assert summary["end"] == "P008.6"
    assert summary["total"] == 50
    assert summary["completed"] == 4
    assert summary["planned"] == 46
    assert summary["roots"] == 8


def test_root_numbers_are_contiguous() -> None:
    assert [record["number"] for record in data.ROOT_MILESTONES] == [
        f"P{number:03d}" for number in range(1, 9)
    ]


def test_stable_record_ids_are_unique_and_deterministic() -> None:
    identifiers = [record["record_id"] for record in data.MILESTONES]
    assert len(identifiers) == len(set(identifiers))
    item = data.get_milestone("P004.2")
    assert item["record_id"] == data._stable_record_id(item["semantic_path"])
    assert item["record_id"].startswith("nxl-pwa-rm-")


def test_lookup_supports_visible_and_stable_identity() -> None:
    visible = data.get_milestone("P008.3")
    stable = data.get_milestone(visible["record_id"])
    assert stable is visible


def test_unknown_lookup_fails_cleanly() -> None:
    with pytest.raises(KeyError, match="roadmap milestone was not found"):
        data.get_milestone("P999")


def test_children_and_descendants_preserve_hierarchy() -> None:
    children = data.get_children("P001")
    descendants = data.get_descendants("P001")
    assert [item["number"] for item in children] == ["P001.1", "P001.2", "P001.3"]
    assert descendants == children


def test_parser_rejects_duplicate_numbers() -> None:
    with pytest.raises(ValueError, match="duplicate roadmap number"):
        data._parse_outline(["P|P001|One", "P|P001|Two"])


def test_parser_rejects_missing_parent() -> None:
    with pytest.raises(ValueError, match="missing parent P001"):
        data._parse_outline(["P|P001.1|Child"])


def test_parser_rejects_unsupported_status() -> None:
    with pytest.raises(ValueError, match="unsupported roadmap status code"):
        data._parse_outline(["X|P001|Invalid"])
