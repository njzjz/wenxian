"""Tests for the title search functionality with real API calls."""

from __future__ import annotations

import pytest

from wenxian.feeder.crossref import Crossref
from wenxian.feeder.semanticscholar import Semanticscholar
from wenxian.from_identifier import from_title


class TestCrossrefTitleSearch:
    """Test Crossref title search with real API."""

    def test_from_title_success(self):
        """Test successful title search returns tuple."""
        feeder = Crossref()
        result = feeder.from_title("Deep residual learning for image recognition")

        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        assert result[0] == "DOI"
        assert isinstance(result[1], str)


class TestSemanticScholarTitleSearch:
    """Test Semantic Scholar title search with real API."""

    def test_from_title_with_doi(self):
        """Test title search that returns a DOI."""
        feeder = Semanticscholar()
        result = feeder.from_title("Attention is all you need")

        assert result is not None
        assert isinstance(result, tuple)
        assert len(result) == 2
        # Should return DOI, PMID, or ARXIV
        assert result[0] in ("DOI", "PMID", "ARXIV")
        assert isinstance(result[1], str)


class TestFromTitle:
    """Test the from_title function with real API."""

    def test_from_title_real_api(self):
        """Test from_title with real API calls."""
        result = from_title("Deep residual learning for image recognition")

        assert result is not None
        assert not result.is_empty()
        assert result.title is not None
