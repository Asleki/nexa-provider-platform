from registries.relationships import RegistryReference, RelationshipDefinition, RelationshipType


def make(runtime_mode):
    return RelationshipDefinition(
        f"rel-{runtime_mode}",
        RelationshipType("type.resides_in", "RESIDENCY.RESIDES_IN", "Resides In"),
        RegistryReference("citizen.registry", "NVG-CIT-1"),
        RegistryReference("district.registry", "NVG-DST-1"),
        runtime_mode,
    )


def test_simulation_and_production_relationships_are_distinguishable():
    simulation = make("simulation")
    production = make("production")
    assert simulation.runtime_mode == "simulation"
    assert production.runtime_mode == "production"
    assert simulation.to_dict() != production.to_dict()


def test_runtime_mode_is_data_scope_not_deployment_environment_enum():
    value = make("simulation")
    assert isinstance(value.runtime_mode, str)
    assert value.runtime_mode != "development"
