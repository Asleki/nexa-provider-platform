"""Unit tests for the PWA roadmap command-line interface."""
import json

import pwa_roadmap


def test_verify_integrity_passes_for_canonical_dataset() -> None:
    assert pwa_roadmap.verify_integrity() == []


def test_dashboard_reports_canonical_totals(capsys) -> None:
    assert pwa_roadmap.main(["dashboard"]) == 0
    output = capsys.readouterr().out
    assert "Canonical records : 50" in output
    assert "Root milestones   : 8" in output
    assert "P001 → P008.6" in output


def test_show_returns_json_for_visible_number(capsys) -> None:
    assert pwa_roadmap.main(["show", "P001.2"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["number"] == "P001.2"
    assert payload["title"] == "Repository, Frontend and Roadmap Governance"


def test_tree_includes_root_and_descendants(capsys) -> None:
    assert pwa_roadmap.main(["tree", "P001"]) == 0
    output = capsys.readouterr().out
    assert "P001 — NexiLabs PWA Project Foundation" in output
    assert "P001.3 — Foundation Verification and Operating Rules" in output


def test_unknown_show_returns_invalid_exit(capsys) -> None:
    assert pwa_roadmap.main(["show", "P999"]) == pwa_roadmap.EXIT_INVALID
    assert "roadmap milestone was not found" in capsys.readouterr().err


def test_json_summary_is_machine_readable(capsys) -> None:
    assert pwa_roadmap.main(["json", "--summary"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["total"] == 50
    assert payload["roots"] == 8
