from database.reference_qualification.contracts import ProductionNameQualificationRequest
from database.reference_qualification.production_name_qualifier import ProductionNameAuthoringQualifier
from registries.name_authority.manual import ProductionManualNameService
from registries.name_authority.repositories.memory import MemoryManualNameCandidateRepository
from registries.names import CanonicalName, MemoryNameRepository, NameKind, NameMetadata


def test_m009_13_10_production_and_simulation_can_coexist_without_identity_rewrite():
    names=MemoryNameRepository()
    names.add(CanonicalName("name:simulation:jordan", "Jordan", NameKind.FIRST_NAME, NameMetadata(runtime_mode="simulation")))
    candidates=MemoryManualNameCandidateRepository()
    report=ProductionNameAuthoringQualifier(
        ProductionManualNameService(names,candidates), names, candidates
    ).qualify(ProductionNameQualificationRequest(
        raw_name_value="  Jordan  ", requested_name_kind="first_name", sex_usage="unisex",
        submitter_actor_id="operator:1", approver_actor_id="approver:1", qualification_id="runtime-isolation",
    ))
    assert report.production_match_count==1
    assert report.simulation_match_count==1
    assert names.count()==2
    assert report.canonical_name_id!="name:simulation:jordan"
