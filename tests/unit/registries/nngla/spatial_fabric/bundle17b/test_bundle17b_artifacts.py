from pathlib import Path
import csv

from registries.nngla.spatial_fabric.bundle17b.artifacts import (
    ARTIFACT_PATHS,
    artifact_contract_findings,
    artifact_paths,
    write_bundle17b_artifacts,
)


def _count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def test_bundle17b_persists_exactly_the_eight_locked_csv_contracts_with_expected_row_counts():
    expected = {
        "crs_crosswalk": 27,
        "precision": 10644,
        "containment": 2411,
        "evidence_types": 5,
        "resolution_policy": 11,
        "environment_bindings": 1104,
        "source_fidelity": 5322,
        "environment_coverage": 1104,
    }
    assert set(ARTIFACT_PATHS) == set(expected)
    assert artifact_contract_findings() == ()
    for key, count in expected.items():
        assert ARTIFACT_PATHS[key].is_file()
        assert _count(ARTIFACT_PATHS[key]) == count


def test_bundle17b_artifact_generation_is_byte_deterministic(tmp_path):
    target = tmp_path / "source"
    generated = write_bundle17b_artifacts(target)
    expected_paths = artifact_paths(target)
    assert set(generated) == set(expected_paths.values())
    for key, generated_path in expected_paths.items():
        assert generated_path.read_bytes() == ARTIFACT_PATHS[key].read_bytes()
