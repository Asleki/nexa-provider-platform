import json
from pathlib import Path
from infrastructure.geography.derivatives import validate_public_boundary_derivative
from infrastructure.geography.refinement import qualify_v002_boundary
ROOT=Path(__file__).parents[4]; BOUNDARY_ROOT=ROOT/'data/novegeo/geography/world-boundary'

def test_10b_pipeline_qualifies_v002_and_materializes_traceable_derivatives_without_runtime_switch():
    qualification=qualify_v002_boundary(BOUNDARY_ROOT)
    for name in ('standard','overview'):
        doc=json.loads((BOUNDARY_ROOT/f'derivatives/v002/novegeo_world_boundary_v002_{name}.geojson').read_text())
        validate_public_boundary_derivative(doc, qualification)
        props=doc['features'][0]['properties']
        assert props['sourceBoundaryVersion']==2
        assert props['sourceQualificationReceiptSha256']==qualification.receipt_sha256
    assert (BOUNDARY_ROOT/'publication/novegeo_world_boundary_v001.geojson').is_file()
    assert not (BOUNDARY_ROOT/'publication/novegeo_world_boundary_v002.geojson').exists()
