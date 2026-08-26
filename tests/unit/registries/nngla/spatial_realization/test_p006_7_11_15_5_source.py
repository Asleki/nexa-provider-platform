from pathlib import Path
from registries.nngla.spatial_realization.source import aggregate_source_sha256,city_roots,source_hashes


def test_locked_source_catalogue_exposes_all_eight_major_city_roots():
    roots=city_roots()
    assert len(roots)==8
    assert [r.place_id for r in roots]==['NG-PLC-000001','NG-PLC-000086','NG-PLC-000173','NG-PLC-000258','NG-PLC-000346','NG-PLC-000432','NG-PLC-000518','NG-PLC-000609']
    assert [r.canonical_name for r in roots]==['Orivane','Northgate','Vondara','Silvermere','Tekharo','Redhaven','Lysora','Port Meridian']
    assert len({r.region_code for r in roots})==8


def test_source_fingerprint_covers_locked_place_admin_topology_and_legalization_evidence():
    rows=source_hashes()
    assert len(rows)==7
    assert all(len(digest)==64 for _,digest in rows)
    paths='\n'.join(path for path,_ in rows)
    assert 'bundle19a/qualified/novegeo_place_reference_points_v001.csv' in paths
    assert 'bundle19b/qualified/novegeo_administrative_boundaries_v001.geojson' in paths
    assert 'novegeo_administrative_topology_policy_v001.csv' in paths
    assert len(aggregate_source_sha256())==64


def test_production_package_contains_no_orivane_specific_execution_constant():
    package=Path('registries/nngla/spatial_realization')
    prohibited=('Orivane','NG-PLC-000001','NG-ADM-000009','NG-SPT-000629','0.892533')
    for source in package.glob('*.py'):
        body=source.read_text(encoding='utf-8')
        for literal in prohibited:
            assert literal not in body, f'{source} contains city-specific production literal {literal}'
