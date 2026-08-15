"""Tests for browser-safe feeder fallbacks."""

from __future__ import annotations

import pytest

from wenxian.from_identifier import _fetch_safely, from_arxiv, from_pmid, from_title
from wenxian.reference import Reference


def _raise(error: Exception):
    """Raise an exception from a callable used by fallback tests."""
    raise error


def test_pmid_falls_back_after_network_error(monkeypatch):
    """Test a PubMed network failure does not abort PMID lookup."""
    monkeypatch.setattr(
        "wenxian.from_identifier.Pubmed.from_pmid",
        lambda *args: _raise(OSError("CORS")),
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
        lambda *args: _raise(OSError("CORS")),
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


def test_browser_catches_javascript_network_exception(monkeypatch):
    """Test Pyodide-only exceptions are treated as feeder failures."""
    monkeypatch.setattr("wenxian.from_identifier.sys.platform", "emscripten")

    result = _fetch_safely(
        "browser", lambda identifier: _raise(RuntimeError("JavaScript error")), "id"
    )

    assert result is None


def test_native_python_does_not_hide_programming_errors(monkeypatch):
    """Test unexpected native Python errors still propagate."""
    monkeypatch.setattr("wenxian.from_identifier.sys.platform", "linux")

    with pytest.raises(RuntimeError, match="programming error"):
        _fetch_safely(
            "native",
            lambda identifier: _raise(RuntimeError("programming error")),
            "id",
        )


def test_title_falls_back_to_semantic_scholar(monkeypatch):
    """Test title lookup falls back when Crossref is unavailable."""
    title = "Fallback title"
    monkeypatch.setattr(
        "wenxian.from_identifier.Crossref.from_title",
        lambda *args: _raise(OSError("CORS")),
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Semanticscholar.from_title",
        lambda *args: "10.1234/example",
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.from_identifier",
        lambda identifier: Reference(title=title, journal="Journal"),
    )

    result = from_title(title)
    assert result is not None
    assert result.title == title


def test_title_returns_none_when_search_sources_fail(monkeypatch):
    """Test title lookup returns None when all search sources fail."""
    monkeypatch.setattr(
        "wenxian.from_identifier.Crossref.from_title", lambda *args: None
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Semanticscholar.from_title", lambda *args: None
    )

    assert from_title("Missing title") is None
