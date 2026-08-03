from database.reference_qualification.contracts import ProductionNameQualificationRequest
from database.reference_qualification.production_name_qualifier import ProductionNameAuthoringQualifier
from registries.name_authority.manual import ProductionManualNameService
from registries.name_authority.repositories.memory import MemoryManualNameCandidateRepository
from registries.names import MemoryNameRepository


def test_production_qualifier_normalizes_reuses_duplicate_and_preserves_runtime_boundary():
    names = MemoryNameRepository()
    candidates = MemoryManualNameCandidateRepository()
    qualifier = ProductionNameAuthoringQualifier(
        ProductionManualNameService(names, candidates), names, candidates
    )
    report = qualifier.qualify(
        ProductionNameQualificationRequest(
            raw_name_value="  Jose\u0301   Maria  ",
            requested_name_kind="first_name",
            sex_usage="male",
            submitter_actor_id="operator:1",
            approver_actor_id="approver:1",
            qualification_id="unicode-normalization",
            language_label="Spanish",
        )
    )
    assert report.passed
    assert report.canonical_value == "José Maria"
    assert report.search_value == "josé maria"
    assert report.runtime_mode == "production"
    assert report.duplicate_outcome == "reused_existing_canonical_name"
    assert report.production_match_count == 1
    assert report.simulation_match_count == 0
    assert names.count() == 1
