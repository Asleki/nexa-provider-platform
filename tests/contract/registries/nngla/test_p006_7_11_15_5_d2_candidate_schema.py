from pathlib import Path

ROOT=Path(__file__).resolve().parents[4]
SQL=(ROOT/'database/migrations/m006_07_11_nngla_shared_face_candidate_lifecycle.sql').read_text()


def test_delivery2_schema_has_candidate_surfaces_and_no_canonical_mutation_statements():
    for table in (
        'nngla_shared_face_fabric_run','nngla_shared_face_fabric_input','nngla_shared_face_edge_candidate',
        'nngla_shared_face_face_candidate','nngla_shared_face_governance_decision','nngla_shared_face_geometry_candidate',
        'nngla_shared_face_qualification_decision'):
        assert f'CREATE TABLE geography.{table}' in SQL
    forbidden=(
        'INSERT INTO geography.nngla_geometry_version','INSERT INTO geography.nngla_geometry_authority_record',
        'UPDATE geography.nngla_administrative_area','nngla_reserve_geometry_id(',
    )
    assert not any(token in SQL for token in forbidden)


def test_delivery2_repository_exposes_no_authority_writer_operations():
    source=(ROOT/'registries/nngla/spatial_realization/candidate_lifecycle/repository.py').read_text()
    for token in ('def reserve_geometry(', 'def supersede(', 'def associate(', 'nngla_reserve_geometry_id('):
        assert token not in source
