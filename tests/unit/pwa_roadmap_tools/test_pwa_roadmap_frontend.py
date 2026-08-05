"""Unit tests for the deterministic PWA roadmap frontend generator."""
from pathlib import Path

import pytest

import pwa_roadmap_frontend as frontend


def test_render_is_deterministic_and_uses_current_totals() -> None:
    first = frontend.render()
    second = frontend.render()
    assert first == second
    assert "Version 0.2.0" in first
    assert "50 canonical records" in first
    assert "8 completed" in first
    assert "42 planned" in first


def test_render_contains_locked_boundaries_and_all_roots() -> None:
    rendered = frontend.render()
    assert "never direct PostgreSQL" in rendered
    for number in range(1, 9):
        assert f"P{number:03d}" in rendered


def test_progress_bar_validates_inputs() -> None:
    with pytest.raises(frontend.PwaRoadmapFrontendError):
        frontend.progress_bar(2, 1)
    with pytest.raises(frontend.PwaRoadmapFrontendError):
        frontend.progress_bar(0, 1, width=0)


def test_write_and_check_round_trip(tmp_path: Path) -> None:
    output = tmp_path / "PWA_ROADMAP.md"
    rendered = frontend.write(output)
    assert output.read_text(encoding="utf-8") == rendered
    assert frontend.write(output, check=True) == rendered


def test_check_rejects_missing_or_stale_output(tmp_path: Path) -> None:
    output = tmp_path / "PWA_ROADMAP.md"
    with pytest.raises(frontend.PwaRoadmapFrontendError, match="does not exist"):
        frontend.write(output, check=True)
    output.write_text("stale\n", encoding="utf-8")
    with pytest.raises(frontend.PwaRoadmapFrontendError, match="out of date"):
        frontend.write(output, check=True)


def test_main_generates_and_checks_custom_output(tmp_path: Path, capsys) -> None:
    output = tmp_path / "roadmap.md"
    assert frontend.main(["--output", str(output)]) == 0
    assert "Generated" in capsys.readouterr().out
    assert frontend.main(["--output", str(output), "--check"]) == 0
    assert "Verified" in capsys.readouterr().out
