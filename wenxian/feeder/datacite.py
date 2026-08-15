"""Feeder for the DataCite REST API."""

from __future__ import annotations

from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION, async_get
from wenxian.reference import Author, BibtexType, Reference


class Datacite(Feeder):
    """Feeder for the DataCite REST API."""

    API_URL = "https://api.datacite.org/dois"
    ARXIV_DOI_PREFIX = "10.48550/arXiv."

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""
        r = SESSION.get(f"{self.API_URL}/{doi}")
        if r.status_code != 200:
            return None
        data = r.json().get("data", {}).get("attributes", {})
        if not data:
            return None
        return self._from_attributes(data, doi=doi)

    async def async_from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI asynchronously."""
        r = await async_get(f"{self.API_URL}/{doi}")
        if r.status_code != 200:
            return None
        data = r.json().get("data", {}).get("attributes", {})
        if not data:
            return None
        return self._from_attributes(data, doi=doi)

    def from_arxiv(self, arxiv: str) -> Reference | None:
        """Fetch a reference from an arXiv identifier."""
        doi = f"{self.ARXIV_DOI_PREFIX}{arxiv}"
        reference = self.from_doi(doi)
        if reference is None:
            return None
        reference.journal = "arXiv"
        reference.pages = arxiv
        return reference

    async def async_from_arxiv(self, arxiv: str) -> Reference | None:
        """Fetch a reference from an arXiv identifier asynchronously."""
        doi = f"{self.ARXIV_DOI_PREFIX}{arxiv}"
        reference = await self.async_from_doi(doi)
        if reference is None:
            return None
        reference.journal = "arXiv"
        reference.pages = arxiv
        return reference

    def _from_attributes(self, data: dict, doi: str) -> Reference:
        """Convert DataCite attributes into a reference."""
        authors = []
        for item in data.get("creators", []):
            first = item.get("givenName")
            last = item.get("familyName")
            if last is None and item.get("name"):
                name = item["name"]
                if "," in name:
                    last, first = (part.strip() for part in name.split(",", 1))
                else:
                    parts = name.split()
                    first = " ".join(parts[:-1])
                    last = parts[-1]
            if first is not None and last is not None:
                authors.append(Author(first=first, last=last))

        titles = data.get("titles") or []
        title = titles[0].get("title") if titles else None
        container = data.get("container") or {}
        journal = container.get("title") or data.get("publisher")

        descriptions = data.get("descriptions") or []
        abstract = next(
            (
                item.get("description")
                for item in descriptions
                if item.get("descriptionType") == "Abstract"
            ),
            None,
        )

        type_name = (data.get("types") or {}).get("bibtex", "article")
        try:
            bibtex_type = BibtexType[type_name]
        except KeyError:
            bibtex_type = BibtexType.article

        pages = None
        first_page = container.get("firstPage")
        last_page = container.get("lastPage")
        if first_page and last_page:
            pages = self._pages(f"{first_page}-{last_page}")
        elif first_page:
            pages = self._pages(str(first_page))

        return Reference(
            author=authors or None,
            title=title,
            journal=journal,
            year=self._int(data.get("publicationYear")),
            volume=self._int(container.get("volume")),
            issue=self._int(container.get("issue")),
            pages=pages,
            annote=abstract,
            doi=data.get("doi") or doi,
            type=bibtex_type,
        )
