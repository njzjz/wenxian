"""Regression tests for title-search validation fallback."""

from __future__ import annotations

import asyncio

import wenxian.from_identifier as identifier_module
from wenxian.reference import Reference


def test_title_mismatch_falls_back_to_semantic_scholar(monkeypatch):
    """Test a mismatched Crossref hit does not stop title fallback."""
    query = "A specific matching paper title"
    semantic_calls = []

    monkeypatch.setattr(
        identifier_module.Crossref,
        "from_title",
        lambda self, title: "10.1234/wrong",
    )

    def semantic(self, title):
        semantic_calls.append(title)
        return "10.1234/right"

    monkeypatch.setattr(identifier_module.Semanticscholar, "from_title", semantic)

    def lookup(identifier):
        if identifier == "10.1234/wrong":
            return Reference(title="A completely unrelated result")
        return Reference(title=query)

    monkeypatch.setattr(identifier_module, "from_identifier", lookup)

    assert identifier_module.from_title(query) == Reference(title=query)
    assert semantic_calls == [query]


def test_async_title_mismatch_falls_back_to_semantic_scholar(monkeypatch):
    """Test async title lookup follows the same validation fallback behavior."""
    query = "A specific matching paper title"
    semantic_calls = []

    async def crossref(self, title):
        return "10.1234/wrong"

    async def semantic(self, title):
        semantic_calls.append(title)
        return "10.1234/right"

    async def lookup(identifier):
        if identifier == "10.1234/wrong":
            return Reference(title="A completely unrelated result")
        return Reference(title=query)

    monkeypatch.setattr(identifier_module.Crossref, "async_from_title", crossref)
    monkeypatch.setattr(identifier_module.Semanticscholar, "async_from_title", semantic)
    monkeypatch.setattr(identifier_module, "async_from_identifier", lookup)

    assert asyncio.run(identifier_module.async_from_title(query)) == Reference(title=query)
    assert semantic_calls == [query]
