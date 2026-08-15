from argparse import Namespace

import pytest

from registries.nngla.migration_architecture.execution_cli import _selector
from registries.nngla.migration_architecture.selectors import SelectorKind


def args(
    *,
    field=None,
    equals=None,
    in_values=None,
    exact_id=None,
    after_id=None,
    limit=None,
):
    return Namespace(
        field=field,
        equals=equals,
        in_values=in_values,
        exact_id=exact_id,
        after_id=after_id,
        limit=limit,
    )


def test_cli_selector_returns_none_when_no_override_is_requested():
    assert _selector(args()) is None


def test_cli_selector_preserves_existing_all_selector_pagination():
    selector = _selector(
        args(
            after_id="NGP-000100",
            limit=50,
        )
    )

    assert selector.kind is SelectorKind.ALL
    assert selector.after_id == "NGP-000100"
    assert selector.limit == 50


def test_cli_selector_supports_field_equals():
    selector = _selector(
        args(
            field="place_type_code",
            equals="SUBURB",
        )
    )

    assert selector.kind is SelectorKind.FIELD_EQUALS
    assert selector.field == "place_type_code"
    assert selector.values == ("SUBURB",)


def test_cli_selector_supports_field_in():
    selector = _selector(
        args(
            field="place_type_code",
            in_values=[
                "CITY_DISTRICT",
                "SUBURB",
                "TOWNSHIP",
            ],
        )
    )

    assert selector.kind is SelectorKind.FIELD_IN
    assert selector.field == "place_type_code"
    assert selector.values == (
        "CITY_DISTRICT",
        "SUBURB",
        "TOWNSHIP",
    )


def test_cli_selector_supports_repeated_exact_ids():
    selector = _selector(
        args(
            exact_id=[
                "NGP-000013",
                "NGP-000014",
            ]
        )
    )

    assert selector.kind is SelectorKind.EXACT_IDS
    assert selector.exact_ids == (
        "NGP-000013",
        "NGP-000014",
    )


def test_field_equals_can_be_combined_with_limit():
    selector = _selector(
        args(
            field="place_type_code",
            equals="SUBURB",
            limit=20,
        )
    )

    assert selector.kind is SelectorKind.FIELD_EQUALS
    assert selector.values == ("SUBURB",)
    assert selector.limit == 20


def test_equals_requires_field():
    with pytest.raises(ValueError, match="--equals requires --field"):
        _selector(args(equals="SUBURB"))


def test_in_requires_field():
    with pytest.raises(ValueError, match="--in requires --field"):
        _selector(args(in_values=["SUBURB", "TOWNSHIP"]))


def test_field_without_selector_mode_is_rejected():
    with pytest.raises(
        ValueError,
        match="--field requires --equals or --in",
    ):
        _selector(args(field="place_type_code"))


def test_exact_ids_cannot_be_combined_with_field():
    with pytest.raises(
        ValueError,
        match="--field cannot be combined with --exact-id",
    ):
        _selector(
            args(
                field="place_type_code",
                exact_id=["NGP-000013"],
            )
        )
