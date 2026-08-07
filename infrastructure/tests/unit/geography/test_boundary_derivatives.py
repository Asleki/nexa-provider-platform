from pathlib import Path
from infrastructure.geography.derivatives import STANDARD_DERIVATIVE, OVERVIEW_DERIVATIVE, build_public_boundary_derivative, validate_public_boundary_derivative
from infrastructure.geography.refinement import qualify_v002_boundary
ROOT=Path(__file__).parents[4]; BOUNDARY_ROOT=ROOT/'data/novegeo/geography/world-boundary'

def test_standard_and_overview_derivatives_reduce_detail_without_losing_islands():
    qualification=qualify_v002_boundary(BOUNDARY_ROOT)
    standard=build_public_boundary_derivative(BOUNDARY_ROOT, STANDARD_DERIVATIVE, qualification)
    overview=build_public_boundary_derivative(BOUNDARY_ROOT, OVERVIEW_DERIVATIVE, qualification)
    for document in (standard, overview): validate_public_boundary_derivative(document, qualification)
    sp=standard['features'][0]['properties']; op=overview['features'][0]['properties']
    assert sp['sourceVertexCount']==1048
    assert 100 < op['derivativeVertexCount'] < sp['derivativeVertexCount'] < 1048
    assert sp['offshoreIslandCount']==op['offshoreIslandCount']==5
    assert sp['runtimePublicationDeferredTo']==op['runtimePublicationDeferredTo']=='P004.M1.5'
