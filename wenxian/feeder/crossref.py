"""Feeder for Crossref API."""

from __future__ import annotations

import html

from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION, async_get
from wenxian.reference import Author, BibtexType, Reference


class Crossref(Feeder):
    """Feeder for Crossref API."""

    API_URL = "https://api.crossref.org/works"

    @staticmethod
    def _identifier_from_title_data(data: dict) -> str | None:
        """Extract the best DOI from a Crossref title-search response."""
        items = data.get("message", {}).get("items", [])
        if not items:
            return None
        return items[0].get("DOI")

    def from_title(self, title: str) -> str | None:
        """Search for a paper by title and return its identifier."""
        r = SESSION.get(
            self.API_URL,
            params={"query.title": title, "rows": "1"},
        )
        if r.status_code != 200:
            return None
        return self._identifier_from_title_data(r.json())

    async def async_from_title(self, title: str) -> str | None:
        """Search for a paper by title asynchronously."""
        r = await async_get(
            self.API_URL,
            params={"query.title": title, "rows": "1"},
        )
        if r.status_code != 200:
            return None
        return self._identifier_from_title_data(r.json())

    def _from_doi_data(self, data: dict, doi: str) -> Reference:
        """Convert Crossref work metadata into a reference."""
        m = data["message"]
        if "title" in m:
            title = m["title"][0]
        else:
            title = None
        if "author" in m:
            author = []
            for aa in m["author"]:
                if "name" in aa:
                    author.append(Author(first="", last=aa["name"]))
                else:
                    author.append(Author(first=aa["given"], last=aa["family"]))
        else:
            author = None
        volume = m.get("volume")
        issue = m.get("issue")
        if "page" in m:
            page = m["page"]
        elif "article-number" in m:
            page = m["article-number"]
        else:
            page = None
        abstract = m.get("abstract")

        if "published-print" in m:
            year = m["published-print"]["date-parts"][0][0]
        elif "published-online" in m:
            year = m["published-online"]["date-parts"][0][0]
        else:
            year = None
        if m.get("short-container-title"):
            journal = html.unescape(m["short-container-title"][0])
        elif m.get("container-title"):
            journal = html.unescape(m["container-title"][0])
        else:
            journal = None

        cr_type = m.get("type")
        if cr_type in (
            "book-series",
            "book-set",
            "book-chapter",
            "book-section",
            "book-part",
            "book-track",
        ):
            ref_type = BibtexType.inbook
        elif cr_type == "proceedings-article":
            ref_type = BibtexType.inproceedings
        elif cr_type == "proceedings":
            ref_type = BibtexType.proceedings
        else:
            ref_type = BibtexType.article
        return Reference(
            author=author,
            title=title,
            journal=journal,
            year=self._int(year),
            volume=self._int(volume),
            issue=self._int(issue),
            pages=self._pages(page),
            annote=abstract,
            doi=doi,
            type=ref_type,
        )

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""
        r = SESSION.get(f"{self.API_URL}/{doi}")
        if r.status_code == 404:
            return None
        return self._from_doi_data(r.json(), doi)

    async def async_from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI asynchronously."""
        r = await async_get(f"{self.API_URL}/{doi}")
        if r.status_code == 404:
            return None
        return self._from_doi_data(r.json(), doi)
