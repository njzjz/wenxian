"""Edge-case tests for asynchronous lookup paths."""

from __future__ import annotations

import asyncio

import pytest

import wenxian.from_identifier as identifier_module
from wenxian.feeder import session
from wenxian.feeder.arxiv import Arxiv
from wenxian.feeder.chemrxiv import Chemrxiv
from wenxian.feeder.crossref import Crossref
from wenxian.feeder.datacite import Datacite
from wenxian.feeder.europepmc import Europepmc
from wenxian.feeder.pubmed import Pubmed
from wenxian.feeder.semanticscholar import Semanticscholar
from wenxian.identifier import Identifier
from wenxian.reference import Reference


class _Response:
    """Minimal response object for asynchronous edge-case tests."""

    def __init__(self, data=None, *, status_code: int = 200, content: bytes = b""):
        self._data = data
        self.status_code = status_code
        self.content = content

    def json(self):
        """Return the configured JSON payload."""
        return self._data


def test_safe_fetch_helpers_handle_transport_and_browser_errors(monkeypatch):
    """Test expected failures are isolated while native programming errors escape."""

    def offline(identifier):
        raise OSError("offline")

    async def async_offline(identifier):
        raise OSError("offline")

    assert identifier_module._fetch_safely("test", offline, "id") is None
    assert (
        asyncio.run(identifier_module._async_fetch_safely("test", async_offline, "id"))
        is None
    )

    def broken(identifier):
        raise RuntimeError("broken parser")

    monkeypatch.setattr(identifier_module.sys, "platform", "linux")
    with pytest.raises(RuntimeError, match="broken parser"):
        identifier_module._fetch_safely("test", broken, "id")

    monkeypatch.setattr(identifier_module.sys, "platform", "emscripten")
    assert identifier_module._fetch_safely("test", broken, "id") is None


def test_async_primary_and_fallback_sources(monkeypatch):
    """Test lazy primary returns and concurrent fallback merging."""

    async def primary_pmid(self, identifier):
        return Reference(title="Primary PMID")

    async def forbidden(self, identifier):
        raise AssertionError("fallback should remain lazy")

    monkeypatch.setattr(identifier_module.Pubmed, "async_from_pmid", primary_pmid)
    monkeypatch.setattr(identifier_module.Europepmc, "async_from_pmid", forbidden)
    monkeypatch.setattr(identifier_module.Semanticscholar, "async_from_pmid", forbidden)
    assert asyncio.run(identifier_module.async_from_pmid("37526163")) == Reference(
        title="Primary PMID"
    )

    async def missing_pmid(self, identifier):
        return None

    async def europe(self, identifier):
        return Reference(title="Europe PMC", journal="Journal")

    async def semantic(self, identifier):
        return Reference(annote="Abstract", doi="10.1234/example")

    monkeypatch.setattr(identifier_module.Pubmed, "async_from_pmid", missing_pmid)
    monkeypatch.setattr(identifier_module.Europepmc, "async_from_pmid", europe)
    monkeypatch.setattr(identifier_module.Semanticscholar, "async_from_pmid", semantic)
    assert asyncio.run(identifier_module.async_from_pmid("37526163")) == Reference(
        title="Europe PMC",
        journal="Journal",
        annote="Abstract",
        doi="10.1234/example",
    )

    async def primary_arxiv(self, identifier):
        return Reference(title="Primary arXiv")

    monkeypatch.setattr(identifier_module.Arxiv, "async_from_arxiv", primary_arxiv)
    monkeypatch.setattr(identifier_module.Datacite, "async_from_arxiv", forbidden)
    monkeypatch.setattr(
        identifier_module.Semanticscholar, "async_from_arxiv", forbidden
    )
    assert asyncio.run(identifier_module.async_from_arxiv("2304.09409")) == Reference(
        title="Primary arXiv"
    )


def test_async_identifier_dispatches_all_supported_types(monkeypatch):
    """Test asynchronous dispatch for every supported identifier type."""

    async def doi(identifier):
        return Reference(title=f"doi:{identifier}")

    async def pmid(identifier):
        return Reference(title=f"pmid:{identifier}")

    async def arxiv(identifier):
        return Reference(title=f"arxiv:{identifier}")

    async def title(identifier):
        return Reference(title=f"title:{identifier}")

    monkeypatch.setattr(identifier_module, "async_from_doi", doi)
    monkeypatch.setattr(identifier_module, "async_from_pmid", pmid)
    monkeypatch.setattr(identifier_module, "async_from_arxiv", arxiv)
    monkeypatch.setattr(identifier_module, "async_from_title", title)

    expected = {
        Identifier.DOI: "doi:value",
        Identifier.PMID: "pmid:value",
        Identifier.ARXIV: "arxiv:value",
        Identifier.TITLE: "title:value",
    }
    for identifier_type, expected_title in expected.items():
        monkeypatch.setattr(
            identifier_module,
            "get_identifier_type",
            lambda identifier, kind=identifier_type: kind,
        )
        result = asyncio.run(identifier_module.async_from_identifier("value"))
        assert result is not None
        assert result.title == expected_title

    monkeypatch.setattr(
        identifier_module, "get_identifier_type", lambda identifier: object()
    )
    with pytest.raises(RuntimeError, match="Unknown identifier type"):
        asyncio.run(identifier_module.async_from_identifier("value"))


def test_async_title_uses_semantic_fallback_and_handles_no_match(monkeypatch):
    """Test title lookup falls back to Semantic Scholar and handles exhaustion."""
    semantic_calls = []

    async def missing_crossref(self, title):
        return None

    async def semantic(self, title):
        semantic_calls.append(title)
        return "10.1234/example"

    async def lookup(identifier):
        return Reference(title="A matching paper title")

    monkeypatch.setattr(
        identifier_module.Crossref, "async_from_title", missing_crossref
    )
    monkeypatch.setattr(identifier_module.Semanticscholar, "async_from_title", semantic)
    monkeypatch.setattr(identifier_module, "async_from_identifier", lookup)
    assert asyncio.run(
        identifier_module.async_from_title("A matching paper title")
    ) == Reference(title="A matching paper title")
    assert semantic_calls == ["A matching paper title"]

    async def no_identifier(self, title):
        return None

    monkeypatch.setattr(
        identifier_module.Semanticscholar, "async_from_title", no_identifier
    )
    assert (
        asyncio.run(identifier_module.async_from_title("No matching paper title"))
        is None
    )


def test_spacing_limiter_and_url_helpers(monkeypatch):
    """Test per-loop spacing state and URL construction branches."""
    sleeps = []

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(session.asyncio, "sleep", fake_sleep)

    async def run():
        limiter = session._AsyncSpacingLimiter(1.0)
        await limiter.wait()
        await limiter.wait()

    asyncio.run(run())
    assert len(sleeps) == 1
    assert sleeps[0] > 0
    assert (
        session._url_with_params("https://example.test", None) == "https://example.test"
    )
    assert (
        session._url_with_params("https://example.test", {"query": "a b"})
        == "https://example.test?query=a+b"
    )


def test_async_get_exhausts_browser_retries(monkeypatch):
    """Test browser transport returns the final retry response."""
    calls = []
    sleeps = []

    async def browser_get(url, params):
        calls.append((url, params))
        return session._BrowserResponse(503, b"{}")

    async def fake_sleep(delay):
        sleeps.append(delay)

    monkeypatch.setattr(session.sys, "platform", "emscripten")
    monkeypatch.setattr(session, "_browser_get", browser_get)
    monkeypatch.setattr(session, "_browser_limiter_for", lambda url: None)
    monkeypatch.setattr(session, "_BROWSER_RETRIES", 2)
    monkeypatch.setattr(session, "_BROWSER_BACKOFF", 0.25)
    monkeypatch.setattr(session.asyncio, "sleep", fake_sleep)

    response = asyncio.run(
        session.async_get("https://example.test", params={"query": "value"})
    )
    assert response.status_code == 503
    assert calls == [
        ("https://example.test", {"query": "value"}),
        ("https://example.test", {"query": "value"}),
        ("https://example.test", {"query": "value"}),
    ]
    assert sleeps == [0.25, 0.5]


def test_pubmed_async_status_and_malformed_payloads(monkeypatch):
    """Test PubMed async helpers handle HTTP and payload failures."""
    feeder = Pubmed()

    async def unavailable(url, **kwargs):
        return _Response(status_code=503)

    monkeypatch.setattr("wenxian.feeder.pubmed.async_get", unavailable)
    assert asyncio.run(feeder._async_doi2pmid_pmc("10.1234/example")) is None
    assert asyncio.run(feeder._async_doi2pmid_search("10.1234/example")) is None
    assert asyncio.run(feeder.async_from_pmid("37526163")) is None

    async def malformed(url, **kwargs):
        return _Response({})

    monkeypatch.setattr("wenxian.feeder.pubmed.async_get", malformed)
    assert asyncio.run(feeder._async_doi2pmid_pmc("10.1234/example")) is None
    assert asyncio.run(feeder._async_doi2pmid_search("10.1234/example")) is None
    assert asyncio.run(feeder.async_from_doi("10.1234/example")) is None


def test_semantic_scholar_async_error_paths(monkeypatch):
    """Test Semantic Scholar async search and identifier failures."""
    feeder = Semanticscholar()

    async def offline(url, **kwargs):
        raise OSError("offline")

    monkeypatch.setattr("wenxian.feeder.semanticscholar.async_get", offline)
    assert asyncio.run(feeder.async_from_title("Example title")) is None
    assert asyncio.run(feeder.async_from_doi("10.1234/example")) is None

    async def unavailable(url, **kwargs):
        if url.endswith("/search"):
            return _Response(status_code=503)
        return _Response(status_code=404)

    monkeypatch.setattr("wenxian.feeder.semanticscholar.async_get", unavailable)
    assert asyncio.run(feeder.async_from_title("Example title")) is None
    assert asyncio.run(feeder.async_from_doi("10.1234/example")) is None
    assert feeder._identifier_from_title_data({}) is None


def test_async_feeders_handle_http_misses(monkeypatch):
    """Test remaining asynchronous feeders return no result on misses."""

    async def crossref_get(url, **kwargs):
        status = 503 if url == Crossref.API_URL else 404
        return _Response(status_code=status)

    monkeypatch.setattr("wenxian.feeder.crossref.async_get", crossref_get)
    assert asyncio.run(Crossref().async_from_title("Example title")) is None
    assert asyncio.run(Crossref().async_from_doi("10.1234/example")) is None

    async def arxiv_get(url, **kwargs):
        return _Response(status_code=503)

    monkeypatch.setattr("wenxian.feeder.arxiv.async_get", arxiv_get)
    assert asyncio.run(Arxiv().async_from_arxiv("2304.09409")) is None

    async def chemrxiv_get(url, **kwargs):
        return _Response(status_code=404)

    monkeypatch.setattr("wenxian.feeder.chemrxiv.async_get", chemrxiv_get)
    assert (
        asyncio.run(Chemrxiv().async_from_doi("10.26434/chemrxiv-2024-example")) is None
    )

    async def datacite_unavailable(url, **kwargs):
        return _Response(status_code=503)

    monkeypatch.setattr("wenxian.feeder.datacite.async_get", datacite_unavailable)
    assert asyncio.run(Datacite().async_from_doi("10.1234/example")) is None

    async def datacite_empty(url, **kwargs):
        return _Response({"data": {"attributes": {}}})

    monkeypatch.setattr("wenxian.feeder.datacite.async_get", datacite_empty)
    assert asyncio.run(Datacite().async_from_doi("10.1234/example")) is None

    async def missing_datacite(self, doi):
        return None

    monkeypatch.setattr(Datacite, "async_from_doi", missing_datacite)
    assert asyncio.run(Datacite().async_from_arxiv("2304.09409")) is None

    async def europe_unavailable(url, **kwargs):
        return _Response(status_code=503)

    monkeypatch.setattr("wenxian.feeder.europepmc.async_get", europe_unavailable)
    assert asyncio.run(Europepmc().async_from_pmid("37526163")) is None

    async def europe_empty(url, **kwargs):
        return _Response({"resultList": {"result": []}})

    monkeypatch.setattr("wenxian.feeder.europepmc.async_get", europe_empty)
    assert asyncio.run(Europepmc().async_from_pmid("37526163")) is None
