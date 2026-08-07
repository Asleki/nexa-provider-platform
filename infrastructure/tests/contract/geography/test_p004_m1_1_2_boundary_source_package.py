import json
from pathlib import Path

from infrastructure.geography.authoring import validate_boundary_source_package

ROOT = Path(__file__).parents[4]
BOUNDARY_ROOT = ROOT / "data/novegeo/geography/world-boundary"


def test_v002_source_package_has_governed_candidate_identity_and_provenance():
    package_path = BOUNDARY_ROOT / "provenance/novegeo_world_boundary_v002_source-package.json"
    package = json.loads(package_path.read_text(encoding="utf-8"))
    receipt = validate_boundary_source_package(BOUNDARY_ROOT)

    assert package["boundaryId"] == "boundary:novegeo:sovereign"
    assert package["boundaryVersion"] == 2
    assert package["supersedesBoundaryVersion"] == 1
    assert package["lifecycleStatus"] == "candidate"
    assert package["qualificationDeferredTo"] == "P004.M1.3"
    assert package["publicDerivativeGenerationDeferredTo"] == "P004.M1.4"
    assert package["provenance"]["externalRealWorldBoundarySourceUsed"] is False
    assert receipt.status == "authoring_validated_candidate"
    assert receipt.unique_vertex_count == package["statistics"]["uniqueBoundaryVertexCount"]
    assert receipt.offshore_island_count == package["statistics"]["offshoreIslandCount"]
