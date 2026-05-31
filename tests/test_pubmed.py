"""Tests for the PubMed feeder."""

from __future__ import annotations

from requests.exceptions import JSONDecodeError

from wenxian.feeder.pubmed import Pubmed


class _NonJsonResponse:
    """Minimal response object for non-JSON PubMed replies."""

    status_code = 403

    def json(self):
        """Raise the same exception as requests for invalid JSON bodies."""
        raise JSONDecodeError("Expecting value", "", 0)


def test_doi2pmid_pmc_ignores_non_json_response(monkeypatch):
    """Test non-JSON PMC responses are treated as missing records."""
    monkeypatch.setattr(
        "wenxian.feeder.pubmed.SESSION.get", lambda *args, **kwargs: _NonJsonResponse()
    )

    assert Pubmed()._doi2pmid_pmc("10.1038/s41524-026-02146-2") is None


def test_doi2pmid_search_ignores_non_json_response(monkeypatch):
    """Test non-JSON PubMed search responses are treated as missing records."""
    monkeypatch.setattr(
        "wenxian.feeder.pubmed.SESSION.get", lambda *args, **kwargs: _NonJsonResponse()
    )

    assert Pubmed()._doi2pmid_search("10.1038/s41524-026-02146-2") is None
