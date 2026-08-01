from pathlib import Path
import itertools
from datetime import datetime,timezone
from registries.name_authority import ProductionSeedLoader,GovernedAtomicNameImporter
from registries.names.memory_name_repository import MemoryNameRepository

ROOT=Path(__file__).resolve().parents[4]
SEEDS=ROOT/'database'/'seeds'

def test_all_production_manifests_validate_and_native_seed_imports():
    loader=ProductionSeedLoader(SEEDS)
    manifests=[loader.load_manifest(p) for p in sorted(SEEDS.rglob('manifest.json'))]
    reports=[loader.validate(m) for m in manifests]
    assert len(reports)==4 and sum(len(r.files) for r in reports)==10
    native=next(m for m in manifests if m.source_family=='novegeo_native')
    repo=MemoryNameRepository(); ids=(f'name:{i}' for i in itertools.count(1)); clock=lambda:datetime(2026,8,1,tzinfo=timezone.utc)
    report=GovernedAtomicNameImporter(loader,repo,clock=clock,name_id_factory=lambda:next(ids)).run(native,runtime_mode='simulation')
    assert report.candidate_count==2380 and report.imported_count>0 and report.failed_count==0
    assert repo.count()==report.imported_count
