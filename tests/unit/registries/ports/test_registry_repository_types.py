from registries.ports.registry_repository_types import (
    RegistryRepositoryOperation,
)


def test_operation_members_are_exact_and_stable() -> None:
    assert tuple(
        (member.name, member.value)
        for member in RegistryRepositoryOperation
    ) == (
        ("ADD", "add"),
        ("READ", "read"),
        ("REPLACE", "replace"),
        ("REMOVE", "remove"),
        ("LIST", "list"),
        ("EXISTS", "exists"),
        ("COUNT", "count"),
        ("CLEAR", "clear"),
    )


def test_operation_values_are_unique_and_string_compatible() -> None:
    values = [member.value for member in RegistryRepositoryOperation]
    assert len(values) == len(set(values))
    assert all(isinstance(member, str) for member in RegistryRepositoryOperation)
