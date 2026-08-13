from datetime import date, datetime, timezone
import pytest
from registries.nngla.lifecycle import EffectiveDateRange, SpatialLifecycleStatus, TERMINAL_SPATIAL_STATES, TemporalDimensions, SuccessionReference
from registries.nngla.source import load_lifecycle_definitions

def test_lifecycle_register_preserves_all_governed_states_and_terminal_metadata():
    defs = load_lifecycle_definitions()
    assert len(defs) == 20
    assert {d.status for d in defs} == set(SpatialLifecycleStatus)
    assert {d.status for d in defs if d.terminal_status} == TERMINAL_SPATIAL_STATES
    assert [d.status_rank for d in defs] == list(range(1, 21))

def test_effective_geometry_and_physical_time_are_separate_dimensions():
    t = TemporalDimensions(
        record_effective=EffectiveDateRange(date(2026,8,12)),
        geometry_valid=EffectiveDateRange(date(2027,1,1)),
        physical_origin_time=datetime(2025,1,1,tzinfo=timezone.utc),
    )
    assert t.record_effective.effective_from != t.geometry_valid.effective_from
    assert t.physical_origin_time.date() < t.record_effective.effective_from

def test_invalid_date_ranges_and_self_supersession_are_rejected():
    with pytest.raises(ValueError): EffectiveDateRange(date(2026,2,1), date(2026,1,1))
    with pytest.raises(ValueError): SuccessionReference("NG-GEO-000001", supersedes_id="NG-GEO-000001")
