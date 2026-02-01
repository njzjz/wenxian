"""Tests for the title search functionality."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from wenxian.feeder.crossref import Crossref
from wenxian.feeder.semanticscholar import Semanticscholar
from wenxian.from_identifier import from_arxiv, from_doi, from_pmid, from_title


class TestCrossrefTitleSearch:
    """Test Crossref title search."""

    @patch("wenxian.feeder.crossref.SESSION.get")
    def test_from_title_success(self, mock_get):
        """Test successful title search returns tuple."""
        # Mock the Crossref API response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "message": {
                "items": [
                    {
                        "DOI": "10.1109/CVPR.2016.90",
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        feeder = Crossref()
        result = feeder.from_title("Deep Residual Learning for Image Recognition")

        assert result == ("DOI", "10.1109/CVPR.2016.90")

    @patch("wenxian.feeder.crossref.SESSION.get")
    def test_from_title_no_results(self, mock_get):
        """Test title search with no results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"message": {"items": []}}
        mock_get.return_value = mock_response

        feeder = Crossref()
        result = feeder.from_title("Nonexistent Paper Title")

        assert result is None

    @patch("wenxian.feeder.crossref.SESSION.get")
    def test_from_title_api_error(self, mock_get):
        """Test title search with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        feeder = Crossref()
        result = feeder.from_title("Any Title")

        assert result is None


class TestSemanticScholarTitleSearch:
    """Test Semantic Scholar title search."""

    @patch("wenxian.feeder.semanticscholar.SESSION.get")
    def test_from_title_with_doi(self, mock_get):
        """Test title search that returns a DOI."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "externalIds": {
                        "DOI": "10.1109/CVPR.2016.90",
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        feeder = Semanticscholar()
        result = feeder.from_title("Deep Residual Learning for Image Recognition")

        assert result == ("DOI", "10.1109/CVPR.2016.90")

    @patch("wenxian.feeder.semanticscholar.SESSION.get")
    def test_from_title_with_pmid(self, mock_get):
        """Test title search that returns a PMID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "externalIds": {
                        "PubMed": "12345678",
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        feeder = Semanticscholar()
        result = feeder.from_title("Some Medical Paper")

        assert result == ("PMID", "12345678")

    @patch("wenxian.feeder.semanticscholar.SESSION.get")
    def test_from_title_with_arxiv(self, mock_get):
        """Test title search that returns an arXiv ID."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": [
                {
                    "externalIds": {
                        "ArXiv": "1706.03762",
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        feeder = Semanticscholar()
        result = feeder.from_title("Attention Is All You Need")

        assert result == ("ARXIV", "1706.03762")

    @patch("wenxian.feeder.semanticscholar.SESSION.get")
    def test_from_title_no_results(self, mock_get):
        """Test title search with no results."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}
        mock_get.return_value = mock_response

        feeder = Semanticscholar()
        result = feeder.from_title("Nonexistent Paper Title")

        assert result is None

    @patch("wenxian.feeder.semanticscholar.SESSION.get")
    def test_from_title_api_error(self, mock_get):
        """Test title search with API error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        feeder = Semanticscholar()
        result = feeder.from_title("Any Title")

        assert result is None


class TestFromTitle:
    """Test the from_title function."""

    @patch("wenxian.from_identifier.from_doi")
    @patch.object(Crossref, "from_title")
    def test_from_title_crossref_success_calls_from_doi(self, mock_cr, mock_from_doi):
        """Test from_title when Crossref succeeds, calls from_doi."""
        mock_cr.return_value = ("DOI", "10.1109/CVPR.2016.90")
        mock_from_doi.return_value = MagicMock()

        result = from_title("Test Title")

        assert result is not None
        mock_cr.assert_called_once_with("Test Title")
        mock_from_doi.assert_called_once_with("10.1109/CVPR.2016.90")

    @patch("wenxian.from_identifier.from_doi")
    @patch.object(Crossref, "from_title")
    @patch.object(Semanticscholar, "from_title")
    def test_from_title_semanticscholar_fallback(self, mock_ss, mock_cr, mock_from_doi):
        """Test from_title falls back to Semantic Scholar."""
        mock_cr.return_value = None
        mock_ss.return_value = ("DOI", "10.1109/CVPR.2016.90")
        mock_from_doi.return_value = MagicMock()

        result = from_title("Test Title")

        assert result is not None
        mock_cr.assert_called_once_with("Test Title")
        mock_ss.assert_called_once_with("Test Title")
        mock_from_doi.assert_called_once_with("10.1109/CVPR.2016.90")

    @patch("wenxian.from_identifier.from_pmid")
    @patch.object(Semanticscholar, "from_title")
    @patch.object(Crossref, "from_title")
    def test_from_title_with_pmid_calls_from_pmid(
        self, mock_cr, mock_ss, mock_from_pmid
    ):
        """Test from_title with PMID calls from_pmid."""
        mock_cr.return_value = None
        mock_ss.return_value = ("PMID", "12345678")
        mock_from_pmid.return_value = MagicMock()

        result = from_title("Test Title")

        assert result is not None
        mock_from_pmid.assert_called_once_with("12345678")

    @patch("wenxian.from_identifier.from_arxiv")
    @patch.object(Semanticscholar, "from_title")
    @patch.object(Crossref, "from_title")
    def test_from_title_with_arxiv_calls_from_arxiv(
        self, mock_cr, mock_ss, mock_from_arxiv
    ):
        """Test from_title with arXiv calls from_arxiv."""
        mock_cr.return_value = None
        mock_ss.return_value = ("ARXIV", "1706.03762")
        mock_from_arxiv.return_value = MagicMock()

        result = from_title("Test Title")

        assert result is not None
        mock_from_arxiv.assert_called_once_with("1706.03762")

    @patch.object(Crossref, "from_title")
    @patch.object(Semanticscholar, "from_title")
    def test_from_title_both_fail(self, mock_ss, mock_cr):
        """Test from_title when both sources fail."""
        mock_cr.return_value = None
        mock_ss.return_value = None

        result = from_title("Nonexistent Title")

        # Result should be an empty Reference
        assert result is not None
        assert result.is_empty()
