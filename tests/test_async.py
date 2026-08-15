"""Tests for concurrent and asynchronous source execution."""

from __future__ import annotations

import asyncio
import sys
import threading
from types import ModuleType

import pytest

from wenxian.feeder import session
from wenxian.feeder.arxiv import Arxiv
from wenxian.feeder.chemrxiv import Chemrxiv
from wenxian.feeder.crossref import Crossref
from wenxian.feeder.datacite import Datacite
from wenxian.feeder.europepmc import Europepmc
from wenxian.feeder.pubmed import Pubmed
from wenxian.feeder.semanticscholar import Semanticscholar
from wenxian.from_identifier import (
    _async_fetch_safely,
    async_from_arxiv,
    async_from_doi,
    async_from_identifier,
    async_from_pmid,
    async_from_title,
    from_arxiv,
    from_doi,
    from_pmid,
)
from wenxian.reference import Author, Reference


class _Response:
    """Minimal response object used by feeder tests."""

    def __init__(self, data=None, content: bytes = b"", status_code: int = 200):
        self._data = data
        self.content = content
        self.status_code = status_code

    def json(self):
        """Return the configured JSON payload."""
        return self._data


def test_async_get_native(monkeypatch):
    """Test native async requests through the existing session."""
    calls = []

    def fake_get(url, params=None):
        calls.append((url, params))
        return _Response({"ok": True})

    monkeypatch.setattr(session.SESSION, "get", fake_get)
    response = asyncio.run(session.async_get("https://example.test", params={"a": 1}))
    assert response.json() == {"ok": True}
    assert calls == [("https://example.test", {"a": 1})]


def test_async_get_browser_retries_and_encodes(monkeypatch):
    """Test browser pyfetch parameter encoding, limiting, and retries."""
    calls = []
    waits = []

    class _FetchResponse:
        """Minimal pyfetch response."""

        def __init__(self, status):
            self.status = status

        async def bytes(self):
            """Return a JSON response body."""
            return b'{"ok": true}'

    async def pyfetch(url, **kwargs):
        calls.append((url, kwargs))
        return _FetchResponse(503 if len(calls) == 1 else 200)

    class _Limiter:
        async def wait(self):
            waits.append(True)

    pyodide = ModuleType("pyodide")
    http = ModuleType("pyodide.http")
    http.pyfetch = pyfetch
    pyodide.http = http
    monkeypatch.setitem(sys.modules, "pyodide", pyodide)
    monkeypatch.setitem(sys.modules, "pyodide.http", http)
    monkeypatch.setattr(session.sys, "platform", "emscripten")
    monkeypatch.setattr(session, "_BROWSER_BACKOFF", 0)
    monkeypatch.setattr(session, "_browser_limiter_for", lambda url: _Limiter())

    response = asyncio.run(
        session.async_get("https://example.test?existing=1", params={"query": "a b"})
    )
    assert response.json() == {"ok": True}
    assert len(calls) == 2
    assert calls[0][0] == "https://example.test?existing=1&query=a+b"
    assert calls[0][1] == {"method": "GET"}
    assert len(waits) == 2


def test_browser_limiters_share_ncbi_quota():
    """Test both NCBI endpoints share one browser-side quota."""
    pmc = session._browser_limiter_for(
        "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    )
    eutils = session._browser_limiter_for(
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    )
    assert pmc is eutils
    assert session._browser_limiter_for("https://example.test") is None


def test_sync_doi_sources_are_concurrent_and_ordered(monkeypatch):
    """Test sync DOI lookups run concurrently and merge by source priority."""
    barrier = threading.Barrier(5)

    def make_fetch(reference):
        def fetch(self, identifier):
            barrier.wait(timeout=1)
            return reference

        return fetch

    monkeypatch.setattr(
        "wenxian.from_identifier.Pubmed.from_doi",
        make_fetch(Reference(title="PubMed")),
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Crossref.from_doi",
        make_fetch(Reference(title="Crossref", journal="Journal")),
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Arxiv.from_doi",
        make_fetch(Reference(year=2024)),
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Chemrxiv.from_doi",
        make_fetch(Reference(annote="Abstract")),
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Semanticscholar.from_doi",
        make_fetch(Reference(doi="10.1234/example")),
    )
    assert from_doi("10.1234/example") == Reference(
        title="PubMed",
        journal="Journal",
        year=2024,
        annote="Abstract",
        doi="10.1234/example",
    )


def test_async_doi_sources_are_concurrent_and_ordered(monkeypatch):
    """Test async DOI lookups start together and merge deterministically."""

    async def run():
        started = 0
        all_started = asyncio.Event()

        def make_fetch(reference):
            async def fetch(self, identifier):
                nonlocal started
                started += 1
                if started == 5:
                    all_started.set()
                await asyncio.wait_for(all_started.wait(), timeout=1)
                return reference

            return fetch

        monkeypatch.setattr(
            "wenxian.from_identifier.Pubmed.async_from_doi",
            make_fetch(Reference(title="PubMed")),
        )
        monkeypatch.setattr(
            "wenxian.from_identifier.Crossref.async_from_doi",
            make_fetch(Reference(title="Crossref", journal="Journal")),
        )
        monkeypatch.setattr(
            "wenxian.from_identifier.Arxiv.async_from_doi",
            make_fetch(Reference(year=2024)),
        )
        monkeypatch.setattr(
            "wenxian.from_identifier.Chemrxiv.async_from_doi",
            make_fetch(Reference(annote="Abstract")),
        )
        monkeypatch.setattr(
            "wenxian.from_identifier.Semanticscholar.async_from_doi",
            make_fetch(Reference(doi="10.1234/example")),
        )
        return await async_from_doi("10.1234/example")

    assert asyncio.run(run()) == Reference(
        title="PubMed",
        journal="Journal",
        year=2024,
        annote="Abstract",
        doi="10.1234/example",
    )


def test_primary_sources_remain_lazy(monkeypatch):
    """Test successful primary PMID and arXiv sources skip fallbacks."""
    calls = []

    def primary(self, identifier):
        return Reference(title="Primary", journal="Primary Journal")

    def fallback(self, identifier):
        calls.append(identifier)
        return Reference(title="Fallback")

    monkeypatch.setattr("wenxian.from_identifier.Pubmed.from_pmid", primary)
    monkeypatch.setattr("wenxian.from_identifier.Europepmc.from_pmid", fallback)
    monkeypatch.setattr("wenxian.from_identifier.Semanticscholar.from_pmid", fallback)
    assert from_pmid("37526163") == Reference(
        title="Primary", journal="Primary Journal"
    )

    monkeypatch.setattr("wenxian.from_identifier.Arxiv.from_arxiv", primary)
    monkeypatch.setattr("wenxian.from_identifier.Datacite.from_arxiv", fallback)
    monkeypatch.setattr("wenxian.from_identifier.Semanticscholar.from_arxiv", fallback)
    assert from_arxiv("2304.09409") == Reference(
        title="Primary", journal="Primary Journal"
    )
    assert calls == []


def test_sync_fallback_sources_are_concurrent(monkeypatch):
    """Test sync fallback candidates run concurrently after a miss."""
    barrier = threading.Barrier(2)

    def missing(self, identifier):
        return None

    def europe(self, identifier):
        barrier.wait(timeout=1)
        return Reference(title="Europe PMC", journal="Journal")

    def semantic(self, identifier):
        barrier.wait(timeout=1)
        return Reference(annote="Abstract", doi="10.1234/example")

    monkeypatch.setattr("wenxian.from_identifier.Pubmed.from_pmid", missing)
    monkeypatch.setattr("wenxian.from_identifier.Europepmc.from_pmid", europe)
    monkeypatch.setattr("wenxian.from_identifier.Semanticscholar.from_pmid", semantic)
    assert from_pmid("37526163") == Reference(
        title="Europe PMC",
        journal="Journal",
        annote="Abstract",
        doi="10.1234/example",
    )


def test_async_fallbacks_and_dispatch(monkeypatch):
    """Test async lazy fallbacks, merging, and identifier dispatch."""
    calls = []

    async def missing(self, identifier):
        calls.append("primary")
        return None

    async def datacite(self, identifier):
        calls.append("datacite")
        await asyncio.sleep(0)
        return Reference(title="DataCite", journal="arXiv")

    async def semantic(self, identifier):
        calls.append("semantic")
        await asyncio.sleep(0)
        return Reference(annote="Abstract", doi="10.48550/arXiv.2304.09409")

    monkeypatch.setattr("wenxian.from_identifier.Arxiv.async_from_arxiv", missing)
    monkeypatch.setattr("wenxian.from_identifier.Datacite.async_from_arxiv", datacite)
    monkeypatch.setattr(
        "wenxian.from_identifier.Semanticscholar.async_from_arxiv", semantic
    )
    assert asyncio.run(async_from_arxiv("2304.09409")) == Reference(
        title="DataCite",
        journal="arXiv",
        annote="Abstract",
        doi="10.48550/arXiv.2304.09409",
    )
    assert calls[0] == "primary"
    assert set(calls[1:]) == {"datacite", "semantic"}

    async def doi(identifier):
        return Reference(title=identifier)

    monkeypatch.setattr("wenxian.from_identifier.async_from_doi", doi)
    result = asyncio.run(async_from_identifier("10.1234/example"))
    assert result is not None
    assert result.title == "10.1234/example"


def test_async_title_priority_and_browser_errors(monkeypatch):
    """Test title priority and Pyodide-specific error isolation."""
    semantic_calls = []

    async def crossref(self, title):
        return "10.1234/crossref"

    async def semantic(self, title):
        semantic_calls.append(title)
        return "10.1234/semantic"

    async def doi(identifier):
        return Reference(title="A matching paper title", journal="Journal")

    monkeypatch.setattr("wenxian.from_identifier.Crossref.async_from_title", crossref)
    monkeypatch.setattr(
        "wenxian.from_identifier.Semanticscholar.async_from_title", semantic
    )
    monkeypatch.setattr("wenxian.from_identifier.async_from_doi", doi)
    assert asyncio.run(async_from_title("A matching paper title")) == Reference(
        title="A matching paper title", journal="Journal"
    )
    assert semantic_calls == []

    async def fail(identifier):
        raise ValueError("JavaScript fetch failed")

    monkeypatch.setattr("wenxian.from_identifier.sys.platform", "emscripten")
    assert asyncio.run(_async_fetch_safely("test", fail, "id")) is None


def test_async_crossref(monkeypatch):
    """Test shared parsing in Crossref async methods."""

    async def fake_get(url, **kwargs):
        if url.endswith("/works"):
            return _Response({"message": {"items": [{"DOI": "10.1234/example"}]}})
        return _Response(
            {
                "message": {
                    "title": ["Example"],
                    "author": [{"given": "Ada", "family": "Lovelace"}],
                    "published-online": {"date-parts": [[2024]]},
                    "container-title": ["Journal of Tests"],
                    "type": "journal-article",
                }
            }
        )

    monkeypatch.setattr("wenxian.feeder.crossref.async_get", fake_get)
    assert asyncio.run(Crossref().async_from_title("Example")) == "10.1234/example"
    assert asyncio.run(Crossref().async_from_doi("10.1234/example")) == Reference(
        author=[Author(first="Ada", last="Lovelace")],
        title="Example",
        journal="Journal of Tests",
        year=2024,
        doi="10.1234/example",
    )


def test_async_semantic_scholar(monkeypatch):
    """Test shared parsing in Semantic Scholar async methods."""
    calls = []

    async def fake_get(url, **kwargs):
        calls.append(url)
        if url.endswith("/search"):
            return _Response({"data": [{"externalIds": {"DOI": "10.1234/example"}}]})
        return _Response(
            {
                "authors": [{"name": "Ada Lovelace"}],
                "title": "Example",
                "journal": {"name": "Journal &amp; Tests"},
                "year": 2024,
                "abstract": "Abstract",
                "externalIds": {"DOI": "10.1234/example"},
            }
        )

    monkeypatch.setattr("wenxian.feeder.semanticscholar.async_get", fake_get)
    feeder = Semanticscholar()
    assert asyncio.run(feeder.async_from_title("Example")) == "10.1234/example"
    expected = Reference(
        author=[Author(first="Ada", last="Lovelace")],
        title="Example",
        journal="Journal & Tests",
        year=2024,
        annote="Abstract",
        doi="10.1234/example",
    )
    assert asyncio.run(feeder.async_from_doi("10.1234/example")) == expected
    assert asyncio.run(feeder.async_from_pmid("37526163")) == expected
    assert asyncio.run(feeder.async_from_arxiv("2304.09409")) == expected
    assert any("PMID:37526163" in url for url in calls)
    assert any("ARXIV:2304.09409" in url for url in calls)


def test_async_arxiv_and_chemrxiv(monkeypatch):
    """Test arXiv and ChemRxiv asynchronous response parsing."""
    arxiv_xml = b"""<?xml version='1.0'?>
    <feed xmlns='http://www.w3.org/2005/Atom'>
      <entry>
        <updated>2024-01-02T00:00:00Z</updated>
        <title>Example preprint.</title>
        <summary>Abstract</summary>
        <author><name>Ada Lovelace</name></author>
      </entry>
    </feed>"""

    async def arxiv_get(url, **kwargs):
        return _Response(content=arxiv_xml)

    monkeypatch.setattr("wenxian.feeder.arxiv.async_get", arxiv_get)
    expected_arxiv = Reference(
        author=[Author(first="Ada", last="Lovelace")],
        title="Example preprint",
        journal="arXiv",
        year=2024,
        annote="Abstract",
        pages="2304.09409",
        doi="10.48550/arXiv.2304.09409",
    )
    assert asyncio.run(Arxiv().async_from_arxiv("2304.09409")) == expected_arxiv
    assert (
        asyncio.run(Arxiv().async_from_doi("10.48550/arXiv.2304.09409"))
        == expected_arxiv
    )
    assert asyncio.run(Arxiv().async_from_doi("10.1234/example")) is None

    async def chemrxiv_get(url, **kwargs):
        return _Response(
            {
                "publishedDate": "2024-01-02T00:00:00Z",
                "authors": [{"firstName": "Ada", "lastName": "Lovelace"}],
                "title": "Example preprint",
                "abstract": "Abstract",
            }
        )

    monkeypatch.setattr("wenxian.feeder.chemrxiv.async_get", chemrxiv_get)
    assert asyncio.run(
        Chemrxiv().async_from_doi("10.26434/chemrxiv-2024-example")
    ) == Reference(
        author=[Author(first="Ada", last="Lovelace")],
        title="Example preprint",
        journal="ChemRxiv",
        year=2024,
        annote="Abstract",
        doi="10.26434/chemrxiv-2024-example",
    )
    assert asyncio.run(Chemrxiv().async_from_doi("10.1234/example")) is None


def test_arxiv_missing_entry_returns_none(monkeypatch):
    """Test an empty arXiv feed allows configured fallback sources."""

    async def fake_get(url, **kwargs):
        return _Response(content=b"<feed xmlns='http://www.w3.org/2005/Atom'/>")

    monkeypatch.setattr("wenxian.feeder.arxiv.async_get", fake_get)
    assert asyncio.run(Arxiv().async_from_arxiv("2304.09409")) is None


def test_async_datacite_and_europepmc(monkeypatch):
    """Test DataCite and Europe PMC asynchronous parsing."""

    async def datacite_get(url, **kwargs):
        return _Response(
            {
                "data": {
                    "attributes": {
                        "doi": "10.48550/arXiv.2304.09409",
                        "creators": [
                            {"givenName": "Ada", "familyName": "Lovelace"}
                        ],
                        "titles": [{"title": "Example"}],
                        "publisher": "arXiv",
                        "publicationYear": 2024,
                        "types": {"bibtex": "article"},
                        "container": {},
                    }
                }
            }
        )

    monkeypatch.setattr("wenxian.feeder.datacite.async_get", datacite_get)
    expected = Reference(
        author=[Author(first="Ada", last="Lovelace")],
        title="Example",
        journal="arXiv",
        year=2024,
        doi="10.48550/arXiv.2304.09409",
    )
    assert asyncio.run(
        Datacite().async_from_doi("10.48550/arXiv.2304.09409")
    ) == expected
    expected.pages = "2304.09409"
    assert asyncio.run(Datacite().async_from_arxiv("2304.09409")) == expected

    async def europe_get(url, **kwargs):
        assert kwargs["params"]["query"] == "EXT_ID:37526163 AND SRC:MED"
        return _Response(
            {
                "resultList": {
                    "result": [
                        {
                            "title": "Example",
                            "pubYear": "2024",
                            "authorList": {
                                "author": [
                                    {"firstName": "Ada", "lastName": "Lovelace"}
                                ]
                            },
                            "journalInfo": {
                                "journal": {"title": "Journal of Tests"}
                            },
                            "doi": "10.1234/example",
                        }
                    ]
                }
            }
        )

    monkeypatch.setattr("wenxian.feeder.europepmc.async_get", europe_get)
    assert asyncio.run(Europepmc().async_from_pmid("37526163")) == Reference(
        author=[Author(first="Ada", last="Lovelace")],
        title="Example",
        journal="Journal of Tests",
        year=2024,
        doi="10.1234/example",
    )


def test_async_pubmed_preserves_lazy_identifier_fallback(monkeypatch):
    """Test PubMed DOI conversion uses search only when PMC has no match."""
    calls = []
    xml = b"""<PubmedArticleSet>
    <PubmedArticle>
      <MedlineCitation><Article>
        <ArticleTitle>Example.</ArticleTitle>
        <AuthorList><Author><ForeName>Ada</ForeName><LastName>Lovelace</LastName></Author></AuthorList>
        <Journal><Title>Journal of Tests</Title><JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue></Journal>
      </Article></MedlineCitation>
      <PubmedData><ArticleIdList><ArticleId IdType='doi'>10.1234/example</ArticleId></ArticleIdList></PubmedData>
    </PubmedArticle>
    </PubmedArticleSet>"""

    async def fake_get(url, **kwargs):
        calls.append(url)
        if url == Pubmed.PMC_IDCONV_URL:
            return _Response({"status": "ok", "records": [{"pmid": "37526163"}]})
        if url == Pubmed.ESEARCH_URL:
            return _Response({"esearchresult": {"idlist": ["99999999"]}})
        return _Response(content=xml)

    monkeypatch.setattr("wenxian.feeder.pubmed.async_get", fake_get)
    expected = Reference(
        author=[Author(first="Ada", last="Lovelace")],
        title="Example",
        journal="Journal of Tests",
        year=2024,
        doi="10.1234/example",
    )
    assert asyncio.run(Pubmed().async_from_doi("10.1234/example")) == expected
    assert Pubmed.PMC_IDCONV_URL in calls
    assert Pubmed.ESEARCH_URL not in calls
    assert Pubmed.EFETCH_URL in calls


def test_async_pubmed_search_fallback(monkeypatch):
    """Test PubMed search fallback and missing DOI validation."""
    calls = []
    xml = b"""<PubmedArticleSet><PubmedArticle><MedlineCitation><Article>
    <ArticleTitle>Example.</ArticleTitle><Journal><Title>Journal</Title>
    <JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue></Journal>
    </Article></MedlineCitation><PubmedData><ArticleIdList>
    <ArticleId IdType='doi'>10.1234/example</ArticleId>
    </ArticleIdList></PubmedData></PubmedArticle></PubmedArticleSet>"""

    async def fake_get(url, **kwargs):
        calls.append(url)
        if url == Pubmed.PMC_IDCONV_URL:
            return _Response({"status": "ok", "records": []})
        if url == Pubmed.ESEARCH_URL:
            return _Response({"esearchresult": {"idlist": ["37526163"]}})
        return _Response(content=xml)

    monkeypatch.setattr("wenxian.feeder.pubmed.async_get", fake_get)
    assert asyncio.run(Pubmed().async_from_doi("10.1234/example")) is not None
    assert Pubmed.ESEARCH_URL in calls
    assert asyncio.run(Pubmed().async_from_doi("10.1234/different")) is None


def test_async_invalid_identifier_and_native_exception(monkeypatch):
    """Test invalid identifiers and native programming error propagation."""
    with pytest.raises(ValueError):
        asyncio.run(async_from_identifier("invalid"))

    async def fail(identifier):
        raise RuntimeError("programming error")

    monkeypatch.setattr("wenxian.from_identifier.sys.platform", "linux")
    with pytest.raises(RuntimeError):
        asyncio.run(_async_fetch_safely("test", fail, "id"))


def test_sync_pyodide_falls_back_to_serial_sources(monkeypatch):
    """Test sync Pyodide callers avoid unsupported worker threads."""
    calls = []

    def make_fetch(name):
        def fetch(self, identifier):
            calls.append(name)
            return Reference(title=name) if name == "PubMed" else None

        return fetch

    monkeypatch.setattr("wenxian.from_identifier.sys.platform", "emscripten")
    monkeypatch.setattr(
        "wenxian.from_identifier.Pubmed.from_doi", make_fetch("PubMed")
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Crossref.from_doi", make_fetch("Crossref")
    )
    monkeypatch.setattr("wenxian.from_identifier.Arxiv.from_doi", make_fetch("arXiv"))
    monkeypatch.setattr(
        "wenxian.from_identifier.Chemrxiv.from_doi", make_fetch("ChemRxiv")
    )
    monkeypatch.setattr(
        "wenxian.from_identifier.Semanticscholar.from_doi",
        make_fetch("Semantic Scholar"),
    )
    assert from_doi("10.1234/example").title == "PubMed"
    assert calls == ["PubMed", "Crossref", "arXiv", "ChemRxiv", "Semantic Scholar"]
