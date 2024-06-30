"""Feeder for Crossref API."""

from __future__ import annotations

import html

from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION
from wenxian.reference import Author, Reference


class Crossref(Feeder):
    """Feeder for Crossref API."""

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""
        r = SESSION.get(
            f"https://api.crossref.org/works/{doi}",
        )
        if r.status_code == 404:
            # DOI not found
            return None
        res = r.json()

        m = res["message"]
        # title
        if "title" in m:
            title = m["title"][0]
        else:
            title = None
        # author
        if "author" in m:
            author = []
            for aa in m["author"]:
                author.append(Author(first=aa["given"], last=aa["family"]))
        else:
            author = None
        # volume & issue
        volume = m.get("volume")
        issue = m.get("issue")
        # page
        if "page" in m:
            page = m["page"]
        elif "article-number" in m:
            page = m["article-number"]
        else:
            page = None
        # abstract
        abstract = m.get("abstract")

        # year
        if "published-print" in m:
            year = m["published-print"]["date-parts"][0][0]
        elif "published-online" in m:
            year = m["published-online"]["date-parts"][0][0]
        else:
            year = None
        # journal
        if m.get("short-container-title"):
            journal = m["short-container-title"][0]
            # while not documented, the journal might be HTML escaped, e.g., Journal of Materials Science &amp; Technology
            # https://api.crossref.org/works/10.1016/j.jmst.2023.09.059
            journal = html.unescape(journal)
        else:
            journal = None
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
        )
