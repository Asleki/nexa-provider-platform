from pathlib import Path
import pytest

from infrastructure.geography.publication import (
    MultiResolutionPublicationError,
    build_v002_multi_resolution_publication,
)

ROOT = Path(__file__).parents[4] / "data/novegeo/geography/world-boundary"


def test_v002_publication_exposes_two_distinct_resolution_classes() -> None:
    publication = build_v002_multi_resolution_publication(ROOT)
    assert publication.publication_id == "publication:novegeo:world-boundary:v002"
    assert publication.boundary_version == 2
    assert publication.default_resolution == "standard"
    assert [item.resolution_class for item in publication.representations] == ["overview", "standard"]
    assert publication.select().resolution_class == "standard"
    assert publication.select("overview").vertex_count == 197
    assert publication.select("standard").vertex_count == 493


def test_explicit_unknown_resolution_is_rejected() -> None:
    publication = build_v002_multi_resolution_publication(ROOT)
    with pytest.raises(MultiResolutionPublicationError, match="unsupported map resolution"):
        publication.select("street")
