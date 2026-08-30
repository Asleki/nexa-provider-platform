from registries.nngla.city_containment_qualification.contracts import QualificationBasis
from registries.nngla.city_containment_qualification.postgis import PostGISCityContainmentQualificationEngine
from registries.nngla.city_realization.contracts import CitySourceEvidence, ParentRegionAuthority


class Cursor:
    def __init__(self, row):
        self.row = row
        self.sql = ""
        self.params = ()
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def execute(self, sql, params=()): self.sql = sql; self.params = params
    def fetchone(self): return self.row


class Connection:
    def __init__(self, cursor): self.cursor_ref = cursor
    def cursor(self): return self.cursor_ref


def source():
    return CitySourceEvidence(
        "NG-ADM-000032", "Northgate", "NGR-02", "NGP-000032", "candidate-32",
        "dataset:novegeo:administrative-boundaries", "1", "source.geojson",
        "a" * 64, "b" * 64, "POLYGON",
        {"type": "Polygon", "coordinates": [[[0,0],[1,0],[0,1],[0,0]]]},
    )


def parent():
    return ParentRegionAuthority(
        "NG-ADM-000002", "Aelvar Highlands", "NGR-02",
        "region-geometry:nngla:NG-ADM-000002:v1", "c" * 64,
    )


def row(*, source_covered=False, final_covered=False, source_outside=0.0, final_outside=0.0, area=100.0):
    final_area = area if source_covered else area - 1.0
    return (
        True, True, "POLYGON", source_covered, area, source_outside,
        True, True, "POLYGON", final_covered, final_area,
        final_outside, 40.0,
        {"type":"Polygon","coordinates":[[[0,0],[1,0],[0,1],[0,0]]]},
        {"type":"Point","coordinates":[0.2,0.2]}, True,
    )


def test_contract_keeps_exact_parent_and_one_intersection_without_snap_or_delivery3():
    cursor = Cursor(row(final_covered=True, source_outside=2.0))
    engine = PostGISCityContainmentQualificationEngine(Connection(cursor))
    result = engine.evaluate(source(), parent())
    assert result.qualification_basis is QualificationBasis.SINGLE_INTERSECTION_STRICT_COVERED
    assert cursor.sql.count("ST_Intersection") == 1
    assert "ST_SnapToGrid" not in cursor.sql
    assert "nngla_city_feature_qualification" not in cursor.sql
    assert cursor.params[:3] == (
        parent().region_geometry_id,
        parent().region_id,
        parent().geometry_sha256,
    )


def test_zero_area_difference_qualifies_when_strict_predicate_is_false():
    result = PostGISCityContainmentQualificationEngine(
        Connection(Cursor(row(final_covered=False, final_outside=0.0)))
    ).evaluate(source(), parent())
    assert result.qualification_status.value == "QUALIFIED"
    assert result.qualification_basis is QualificationBasis.SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE


def test_microscopic_residue_qualifies_but_larger_residue_rejects():
    tiny = PostGISCityContainmentQualificationEngine(
        Connection(Cursor(row(final_covered=False, final_outside=0.000012219, area=40_019_360_001.0)))
    ).evaluate(source(), parent())
    assert tiny.qualification_status.value == "QUALIFIED"
    assert tiny.qualification_basis is QualificationBasis.SINGLE_INTERSECTION_NUMERICAL_RESIDUE

    large = PostGISCityContainmentQualificationEngine(
        Connection(Cursor(row(final_covered=False, final_outside=0.01)))
    ).evaluate(source(), parent())
    assert large.qualification_status.value == "REJECTED"
    assert large.qualification_basis is QualificationBasis.REJECTED_RESIDUE_EXCEEDS_POLICY


def test_strictly_covered_source_is_reused_and_qualified_without_intersection_result_change():
    result = PostGISCityContainmentQualificationEngine(
        Connection(Cursor(row(source_covered=True, final_covered=True)))
    ).evaluate(source(), parent())
    assert result.realization_method == "SOURCE_REUSE"
    assert result.qualification_basis is QualificationBasis.STRICT_SOURCE_COVERED


def test_numerical_residue_requires_both_absolute_and_ratio_limits():
    # Tiny absolute area is still rejected when it is too large relative to a tiny final geometry.
    result = PostGISCityContainmentQualificationEngine(
        Connection(Cursor(row(final_covered=False, final_outside=0.0000005, area=1.000001)))
    ).evaluate(source(), parent())
    assert result.normalized_outside_parent_m2 <= 0.001
    assert result.normalized_outside_parent_ratio > 1e-12
    assert result.qualification_status.value == "REJECTED"
    assert result.qualification_basis is QualificationBasis.REJECTED_RESIDUE_EXCEEDS_POLICY


def test_observed_live_city_containment_cases_all_map_to_governed_qualified_bases():
    # Read-only npp_dev comparator evidence captured on 2026-08-30.  These values
    # lock the maintenance defect: valid single-intersection results must not be
    # rejected solely by a strict CoveredBy false when outside polygon area is
    # zero or microscopic under policy v1.
    cases = (
        ("Orivane", False, True, 3.814697265625e-06, 0.0, 22_922_130_486.810425, QualificationBasis.SINGLE_INTERSECTION_STRICT_COVERED),
        ("Northgate", False, False, 7.62939453125e-06, 0.0, 67_428_529_649.24042, QualificationBasis.SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE),
        ("Vondara", False, False, 1.1920928955078125e-07, 1.2218952178955078e-05, 40_019_360_001.29882, QualificationBasis.SINGLE_INTERSECTION_NUMERICAL_RESIDUE),
        ("Silvermere", False, True, 205_477.8334543705, 0.0, 72_354_933_184.6491, QualificationBasis.SINGLE_INTERSECTION_STRICT_COVERED),
        ("Tekharo", False, False, 1.3113021850585938e-05, 0.0, 9_139_876_722.059153, QualificationBasis.SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE),
        ("Redhaven", False, False, 0.0, 0.0, 29_472_672_179.179974, QualificationBasis.SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE),
        ("Lysora", False, False, 0.0, 0.0, 7_884_007_397.157715, QualificationBasis.SINGLE_INTERSECTION_ZERO_AREA_DIFFERENCE),
    )
    for name, source_covered, final_covered, source_outside, final_outside, area, expected_basis in cases:
        result = PostGISCityContainmentQualificationEngine(
            Connection(Cursor(row(
                source_covered=source_covered,
                final_covered=final_covered,
                source_outside=source_outside,
                final_outside=final_outside,
                area=area,
            )))
        ).evaluate(source(), parent())
        assert result.qualification_status.value == "QUALIFIED", name
        assert result.qualification_basis is expected_basis, name
