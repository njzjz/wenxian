"""Feeder for arXiv."""

from __future__ import annotations

import re
from typing import ClassVar
from xml.etree import ElementTree

from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION, async_get
from wenxian.reference import Author, Reference


class Arxiv(Feeder):
    """Feeder for arXiv."""

    ARXIV_PATH: ClassVar[dict[str, str]] = {
        "author": r"{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}author/{http://www.w3.org/2005/Atom}name",
        "title": r"{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}title",
        "abstract": r"{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}summary",
        "updated": r"{http://www.w3.org/2005/Atom}entry/{http://www.w3.org/2005/Atom}updated",
    }
    """XPath for arXiv XML."""
    DOI_PREFIX = "10.48550/arXiv."
    """DOI prefix for arXiv."""

    def _from_content(self, content: bytes, arxiv: str) -> Reference | None:
        """Convert an arXiv Atom response into a reference."""
        tree = ElementTree.fromstring(content)
        entry = tree.find(r"{http://www.w3.org/2005/Atom}entry")
        if entry is None:
            return None

        rets = {}
        for key, path in self.ARXIV_PATH.items():
            if key != "author":
                value = self._text(tree.find(path))
                if value is not None:
                    value = re.sub("[ \n]+", " ", value)
                rets[key] = value
        author = []
        for node in tree.findall(self.ARXIV_PATH["author"]):
            name = self._text(node)
            if name is None:
                continue
            split_name = name.split()
            author.append(Author(first=" ".join(split_name[:-1]), last=split_name[-1]))
        if rets["updated"] is not None:
            year = int(rets["updated"].split("-")[0])
        else:
            year = None

        return Reference(
            author=author or None,
            title=rets["title"].rstrip(".") if rets["title"] is not None else None,
            journal="arXiv",
            year=year,
            annote=rets["abstract"],
            pages=arxiv,
            doi=f"{self.DOI_PREFIX}{arxiv}",
        )

    def from_arxiv(self, arxiv: str) -> Reference | None:
        """Fetch a reference from an arXiv identifier."""
        r = SESSION.get("https://export.arxiv.org/api/query", params={"id_list": arxiv})
        if r.status_code != 200:
            return None
        return self._from_content(r.content, arxiv)

    async def async_from_arxiv(self, arxiv: str) -> Reference | None:
        """Fetch a reference from an arXiv identifier asynchronously."""
        r = await async_get(
            "https://export.arxiv.org/api/query", params={"id_list": arxiv}
        )
        if r.status_code != 200:
            return None
        return self._from_content(r.content, arxiv)

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""
        if not doi.startswith(self.DOI_PREFIX):
            return None
        return self.from_arxiv(doi[len(self.DOI_PREFIX) :])

    async def async_from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI asynchronously."""
        if not doi.startswith(self.DOI_PREFIX):
            return None
        return await self.async_from_arxiv(doi[len(self.DOI_PREFIX) :])
