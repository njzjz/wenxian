"""Feeder for the Semantic Scholar API."""

from __future__ import annotations

import html

from requests.exceptions import RequestException

from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION, async_get
from wenxian.reference import Author, Reference


class Semanticscholar(Feeder):
    """Feeder for Semantic Scholar API."""

    API_URL = "https://api.semanticscholar.org/graph/v1/paper"

    @staticmethod
    def _identifier_from_title_data(data: dict) -> str | None:
        """Extract the preferred external identifier from search data."""
        papers = data.get("data", [])
        if not papers:
            return None
        external_ids = papers[0].get("externalIds", {})
        return (
            external_ids.get("DOI")
            or external_ids.get("PubMed")
            or external_ids.get("ArXiv")
        )

    def from_title(self, title: str) -> str | None:
        """Search for a paper by title and return its identifier."""
        try:
            r = SESSION.get(
                f"{self.API_URL}/search",
                params={"query": title, "limit": "1", "fields": "externalIds"},
            )
        except RequestException:
            return None
        if r.status_code != 200:
            return None
        return self._identifier_from_title_data(r.json())

    async def async_from_title(self, title: str) -> str | None:
        """Search for a paper by title asynchronously."""
        try:
            r = await async_get(
                f"{self.API_URL}/search",
                params={"query": title, "limit": "1", "fields": "externalIds"},
            )
        except (OSError, RequestException):
            return None
        if r.status_code != 200:
            return None
        return self._identifier_from_title_data(r.json())

    @staticmethod
    def _from_data(data: dict) -> Reference:
        """Convert Semantic Scholar metadata into a reference."""
        authors = []
        for author in data["authors"]:
            name = author["name"]
            last = name.split(" ")[-1]
            first = " ".join(name.split(" ")[:-1])
            authors.append(Author(first=first, last=last))
        if data["journal"] is not None and "name" in data["journal"]:
            journal = html.unescape(data["journal"]["name"])
        else:
            journal = None
        external_ids = data.get("externalIds") or {}
        return Reference(
            author=authors,
            title=data["title"],
            journal=journal,
            year=data["year"],
            annote=data["abstract"],
            doi=external_ids.get("DOI"),
        )

    def _from_identifier(self, identifier: str) -> Reference | None:
        """Fetch a reference from an identifier."""
        try:
            r = SESSION.get(
                f"{self.API_URL}/{identifier}",
                params={
                    "fields": "title,year,abstract,authors.name,journal,externalIds"
                },
            )
        except RequestException:
            return None
        if r.status_code == 404:
            return None
        return self._from_data(r.json())

    async def _async_from_identifier(self, identifier: str) -> Reference | None:
        """Fetch a reference from an identifier asynchronously."""
        try:
            r = await async_get(
                f"{self.API_URL}/{identifier}",
                params={
                    "fields": "title,year,abstract,authors.name,journal,externalIds"
                },
            )
        except (OSError, RequestException):
            return None
        if r.status_code == 404:
            return None
        return self._from_data(r.json())

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""
        return self._from_identifier(doi)

    async def async_from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI asynchronously."""
        return await self._async_from_identifier(doi)

    def from_pmid(self, pmid: str | int) -> Reference | None:
        """Fetch a reference from a PMID."""
        return self._from_identifier(f"PMID:{pmid}")

    async def async_from_pmid(self, pmid: str | int) -> Reference | None:
        """Fetch a reference from a PMID asynchronously."""
        return await self._async_from_identifier(f"PMID:{pmid}")

    def from_arxiv(self, arxiv: str) -> Reference | None:
        """Fetch a reference from an arXiv ID."""
        return self._from_identifier(f"ARXIV:{arxiv}")

    async def async_from_arxiv(self, arxiv: str) -> Reference | None:
        """Fetch a reference from an arXiv ID asynchronously."""
        return await self._async_from_identifier(f"ARXIV:{arxiv}")
