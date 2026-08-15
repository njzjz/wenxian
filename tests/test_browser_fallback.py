"""Tests for browser-safe feeder fallbacks."""

from __future__ import annotations

from wenxian.from_identifier import from_arxiv, from_pmid
from wenxian.reference import Reference


def test_pmid_falls_back_after_network_error(monkeypatch):
    """Test a PubMed network failure does not abort PMID lookup."""
    monkeypatch.setattr(
        "wenxian.from_identifier.Pubmed.from_pmid",
        lambda *args: (_ for _ in ()).throw(OSError("CORS")),
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Europepmc.from_pmid",
        lambda *args: Reference(title="Fallback", journal="Journal"),
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Semanticscholar.from_pmid", lambda *args: None
    )

    result = from_pmid("37526163")
    assert result is not None
    assert result.title == "Fallback"


def test_arxiv_falls_back_after_network_error(monkeypatch):
    """Test an arXiv network failure does not abort arXiv lookup."""
    monkeypatch.setattr(
        "wenxian.from_identifier.Arxiv.from_arxiv",
        lambda *args: (_ for _ in ()).throw(OSError("CORS")),
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Datacite.from_arxiv",
        lambda *args: Reference(title="Fallback", journal="arXiv"),
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Semanticscholar.from_arxiv", lambda *args: None
    )

    result = from_arxiv("2304.09409")
    assert result is not None
    assert result.title == "Fallback"
