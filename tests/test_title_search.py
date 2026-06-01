"""Tests for the title search functionality with real API calls."""

from __future__ import annotations

import pytest
from requests.exceptions import RequestException

from wenxian.feeder.crossref import Crossref
from wenxian.feeder.semanticscholar import Semanticscholar
from wenxian.from_identifier import from_identifier

TEST_CASES = [
    (
        Crossref,
        "Deep residual learning for image recognition",
        "10.1109/cvpr.2016.90",
    ),
]


@pytest.mark.parametrize("feeder, title, identifier", TEST_CASES)
def test_feeder_from_title(feeder, title, identifier):
    """Test title search that returns a DOI."""
    assert feeder().from_title(title) == identifier


def test_from_identifier():
    """Test from_identifier with real API calls."""
    _, title, identifier = TEST_CASES[0]
    assert from_identifier(title).doi == identifier


def test_semanticscholar_from_title_ignores_request_errors(monkeypatch):
    """Test Semantic Scholar request failures are treated as missing records."""

    def raise_request_error(*args, **kwargs):
        raise RequestException("too many 429 error responses")

    monkeypatch.setattr(
        "wenxian.feeder.semanticscholar.SESSION.get", raise_request_error
    )

    assert (
        Semanticscholar().from_title("Deep residual learning for image recognition")
        is None
    )
