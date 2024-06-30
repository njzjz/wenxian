"""Feeder for Crossref API."""

from __future__ import annotations

import html

from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION
from wenxian.reference import Author, Reference


class Semanticscholar(Feeder):
    """Feeder for Crossref API."""

    def _from_identifier(self, identifier: str) -> Reference | None:
        """Fetch a reference from a identifier."""
        r = SESSION.get(
            f"https://api.semanticscholar.org/graph/v1/paper/{identifier}",
            params={"fields": "title,year,abstract,authors.name,journal,externalIds"},
        )
        if r.status_code == 404:
            # DOI not found
            return None
        res = r.json()
        authors = []
        for author in res["authors"]:
            name = author["name"]
            last = name.split(" ")[-1]
            first = " ".join(name.split(" ")[:-1])
            authors.append(Author(first=first, last=last))
        # journal may be null, e.g.,
        # https://api.semanticscholar.org/graph/v1/paper/10.1103/PhysRevB.109.174106?fields=title,year,abstract,authors.name,journal,externalIds
        if res["journal"] is not None:
            journal = res["journal"]["name"]
            # the journal might be HTML escaped, e.g., Journal of Materials Science &amp; Technology
            # https://api.semanticscholar.org/graph/v1/paper/10.1016/j.jmst.2023.09.059?fields=title,year,abstract,authors.name,journal,externalIds
            journal = html.unescape(journal)
        else:
            journal = None
        return Reference(
            author=authors,
            title=res["title"],
            journal=journal,
            year=res["year"],
            annote=res["abstract"],
            doi=res["externalIds"]["DOI"],
        )

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""
        return self._from_identifier(doi)

    def from_pmid(self, pmid: str | int) -> Reference | None:
        """Fetch a reference from a PMID."""
        return self._from_identifier(f"PMID:{pmid}")

    def from_arxiv(self, arxiv: str) -> Reference | None:
        """Fetch a reference from an arXiv ID."""
        return self._from_identifier(f"ARXIV:{arxiv}")
