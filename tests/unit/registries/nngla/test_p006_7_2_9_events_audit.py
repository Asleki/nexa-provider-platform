from datetime import datetime, timezone
import pytest

from registries.country.operating_context import RecordEffectScope
from registries.nngla.events import NNGLAEventFactory, NNGLAEventType
from shared.runtime.operation_runtime import OperationRuntimeMode


def test_canonicalization_event_links_shared_audit_without_embedding_authority_record():
    trace = NNGLAEventFactory.create(
        event_type=NNGLAEventType.RECORD_CANONICALIZED,
        subject_id="NG-RD-000123",
        record_family="ROAD_REFERENCE",
        runtime_mode=OperationRuntimeMode.SIMULATION,
        effect_scope=RecordEffectScope.RUNTIME_SCOPED,
        canonical_version=2,
        correlation_id="corr:14c:1",
        actor_id="authority:nngla",
        device_id="device:test",
        occurred_at=datetime(2026, 8, 14, tzinfo=timezone.utc),
        payload={"canonicalization_receipt_id": "canonicalization:nngla:test"},
    )
    assert trace.event.event_type == "NNGLA_RECORD_CANONICALIZED"
    assert trace.event.payload["subject_id"] == "NG-RD-000123"
    assert trace.event.payload["runtime_mode"] == "simulation"
    assert "mandate_summary" not in trace.event.payload
    assert trace.audit.event_id == trace.event.event_id
    assert trace.audit.runtime_mode == "simulation"
    assert trace.audit.target_id == "NG-RD-000123"


def test_event_preserves_runtime_and_effect_scope_as_distinct_dimensions():
    trace = NNGLAEventFactory.create(
        event_type=NNGLAEventType.RECORD_PUBLISHED,
        subject_id="NG-GEO-000001",
        record_family="GEOMETRY",
        runtime_mode="production",
        effect_scope="RUNTIME_SCOPED",
        canonical_version=1,
        correlation_id="corr:14c:2",
        actor_id="authority:nngla",
    )
    assert trace.event.payload["runtime_mode"] == "production"
    assert trace.event.payload["effect_scope"] == "RUNTIME_SCOPED"
    assert trace.audit.metadata["effect_scope"] == "RUNTIME_SCOPED"


def test_event_rejects_incompatible_runtime_effect_scope():
    with pytest.raises(ValueError, match="SIMULATION_ONLY"):
        NNGLAEventFactory.create(
            event_type=NNGLAEventType.RECORD_QUARANTINED,
            subject_id="candidate:1",
            record_family="GEOGRAPHIC_FEATURE",
            runtime_mode="production",
            effect_scope="SIMULATION_ONLY",
            correlation_id="corr:14c:3",
            actor_id="authority:nngla",
        )


def test_event_timestamp_is_distinct_from_domain_effective_time():
    when = datetime(2026, 8, 14, 1, 2, 3, tzinfo=timezone.utc)
    trace = NNGLAEventFactory.create(
        event_type=NNGLAEventType.FOUNDATION_QUALIFIED,
        subject_id="authority:nngla",
        record_family="NNGLA_FOUNDATION",
        runtime_mode="production",
        effect_scope="SHARED_REFERENCE",
        correlation_id="corr:14c:4",
        actor_id="authority:nngla",
        occurred_at=when,
        payload={"effective_from": "2026-08-12"},
    )
    assert trace.event.occurred_at == when
    assert trace.event.payload["effective_from"] == "2026-08-12"
