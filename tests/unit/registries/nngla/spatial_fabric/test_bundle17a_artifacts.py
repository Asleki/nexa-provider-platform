from pathlib import Path
import csv
import shutil

from registries.nngla.spatial_fabric.artifacts import write_derived_artifacts
from registries.nngla.spatial_fabric.source_inventory import MANIFEST_PATH, SOURCE_ROOT


def _count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def test_generated_bundle17a_artifacts_have_locked_row_counts():
    expected = {
        "novegeo_coordinate_occurrences_v002.csv": 5322,
        "novegeo_coordinate_candidates_v002.csv": 2411,
        "novegeo_coordinate_occurrence_crosswalk_v002.csv": 5322,
        "novegeo_spatial_neighbor_topology_v002.csv": 1120,
        "novegeo_spatial_source_contract_results_v001.csv": 47,
        "novegeo_spatial_topology_qualification_results_v001.csv": 1120,
    }
    for name, count in expected.items():
        matches = list(SOURCE_ROOT.rglob(name))
        assert len(matches) == 1
        assert _count(matches[0]) == count


def test_artifact_generation_is_byte_deterministic(tmp_path):
    target = tmp_path / "source"
    (target / "00_manifest").mkdir(parents=True)
    shutil.copy2(MANIFEST_PATH, target / "00_manifest" / MANIFEST_PATH.name)
    generated = write_derived_artifacts(target)
    for name, generated_path in generated.items():
        existing = next(SOURCE_ROOT.rglob(name))
        assert generated_path.read_bytes() == existing.read_bytes()
