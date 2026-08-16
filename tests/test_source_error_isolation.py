"""Tests for isolating expected metadata-source failures."""

from __future__ import annotations

import asyncio

import pytest

import wenxian.from_identifier as identifier_module
from wenxian.reference import Reference


def test_sync_doi_keeps_good_result_when_one_source_has_bad_payload(monkeypatch):
    """Test one malformed source does not discard usable DOI metadata."""
    monkeypatch.setattr(
        identifier_module.Pubmed,
        "from_doi",
        lambda self, doi: Reference(title="Usable", journal="Journal"),
    )
    monkeypatch.setattr(
        identifier_module.Crossref,
        "from_doi",
        lambda self, doi: (_ for _ in ()).throw(KeyError("message")),
    )
    monkeypatch.setattr(identifier_module.Arxiv, "from_doi", lambda self, doi: None)
    monkeypatch.setattr(identifier_module.Chemrxiv, "from_doi", lambda self, doi: None)
    monkeypatch.setattr(
        identifier_module.Semanticscholar, "from_doi", lambda self, doi: None
    )

    assert identifier_module.from_doi("10.1234/example") == Reference(
        title="Usable", journal="Journal"
    )


def test_async_doi_keeps_good_result_when_one_source_has_bad_payload(monkeypatch):
    """Test async aggregation also isolates malformed source payloads."""

    async def good(self, doi):
        return Reference(title="Usable", journal="Journal")

    async def bad(self, doi):
        raise TypeError("malformed payload")

    async def missing(self, doi):
        return None

    monkeypatch.setattr(identifier_module.Pubmed, "async_from_doi", good)
    monkeypatch.setattr(identifier_module.Crossref, "async_from_doi", bad)
    monkeypatch.setattr(identifier_module.Arxiv, "async_from_doi", missing)
    monkeypatch.setattr(identifier_module.Chemrxiv, "async_from_doi", missing)
    monkeypatch.setattr(identifier_module.Semanticscholar, "async_from_doi", missing)

    assert asyncio.run(identifier_module.async_from_doi("10.1234/example")) == Reference(
        title="Usable", journal="Journal"
    )


def test_native_programming_error_still_escapes(monkeypatch):
    """Test unexpected programming errors are not swallowed on native Python."""
    monkeypatch.setattr(identifier_module.sys, "platform", "linux")

    def broken(identifier):
        raise RuntimeError("bug")

    with pytest.raises(RuntimeError, match="bug"):
        identifier_module._fetch_safely("test", broken, "id")
