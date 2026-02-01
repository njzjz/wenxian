"""Tests for the title search functionality with real API calls."""

from __future__ import annotations

from wenxian.feeder.crossref import Crossref
from wenxian.feeder.semanticscholar import Semanticscholar
from wenxian.from_identifier import from_identifier, from_title
from wenxian.identifier import Identifier

import pytest


TEST_CASES = [
    (
        Crossref,
        "Deep residual learning for image recognition",
        Identifier.DOI,
        "10.1109/cvpr.2016.90",
    ),
    (
        Semanticscholar,
        "Deep residual learning for image recognition",
        Identifier.ARXIV,
        "2304.09409",
    ),
]


@pytest.mark.parametrize("feeder, title, itype, identifier", TEST_CASES)
def test_feeder_from_title(feeder, title, itype, identifier):
    """Test title search that returns a DOI."""
    assert feeder().from_title(title) == (itype, identifier)


def test_from_identifier():
    """Test from_identifier with real API calls."""
    _, title, _, identifier = TEST_CASES[0]
    assert from_identifier(title).doi == identifier
