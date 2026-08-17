from __future__ import annotations
from ._shared import EVIDENCE_ROOT

def artifact_paths():
    return {n:EVIDENCE_ROOT/f'{n}_v001.csv' for n in ('novegeo_allocator_concurrency_scenarios','novegeo_allocator_collision_cases','novegeo_allocator_recovery_cases','novegeo_allocator_expected_results','novegeo_allocator_stress_results')}
__all__=['artifact_paths']
