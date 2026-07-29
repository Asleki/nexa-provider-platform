from tests.unit.registries.metadata.metadata_test_support import (
    make_capability,
    make_profile,
    make_provenance,
)


def test_simulation_and_production_support_remain_independent():
    simulation = make_capability(
        capability_id="simulation-seed",
        capability_code="SIMULATION.SEED",
        category="simulation",
        simulation_supported=True,
        production_supported=False,
    )
    production = make_capability(
        capability_id="production-register",
        capability_code="IDENTITY.REGISTER",
        category="identity",
        simulation_supported=False,
        production_supported=True,
    )
    profile = make_profile(capabilities=(simulation, production))
    assert profile.capabilities[0].simulation_supported is True
    assert profile.capabilities[0].production_supported is False
    assert profile.capabilities[1].simulation_supported is False
    assert profile.capabilities[1].production_supported is True


def test_runtime_reference_attribute_does_not_become_runtime_state():
    profile = make_profile(attributes={"runtime_mode_reference": "simulation"})
    assert not hasattr(profile, "runtime_mode")
    assert profile.attributes["runtime_mode_reference"] == "simulation"


def test_simulation_generator_provenance_can_be_declared_without_execution():
    profile = make_profile(
        capabilities=(
            make_capability(
                capability_id="simulation-seed",
                capability_code="SIMULATION.SEED",
                category="simulation",
            ),
        ),
        provenance=make_provenance(
            source_type="simulation_generator",
            source_system="nexilabs-generator",
            generated=True,
            generator_name="population-generator",
            generation_batch_id="NVG-FOUNDATION-0001",
        ),
    )
    assert profile.provenance.generated is True
    assert profile.provenance.generation_batch_id == "NVG-FOUNDATION-0001"
