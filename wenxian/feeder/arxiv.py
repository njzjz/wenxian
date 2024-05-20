"""Feeder for arXiv."""

from __future__ import annotations

import re
from typing import ClassVar
from xml.etree import ElementTree

from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION
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

    def from_arxiv(self, arxiv: str) -> Reference | None:
        """Fetch a reference from an arXiv identifier."""
        r = SESSION.get("https://export.arxiv.org/api/query", params={"id_list": arxiv})

        tree = ElementTree.fromstring(r.content)

        rets = {}
        for key, path in self.ARXIV_PATH.items():
            if key not in ("author",):
                rr = self._text(tree.find(path))
                if rr is not None:
                    rr = re.sub("[ \n]+", " ", rr)
                rets[key] = rr
        author_tree = tree.findall(self.ARXIV_PATH["author"])
        if author_tree is not None:
            author = []
            for aa in author_tree:
                split_name = self._text(aa).split()
                author.append(
                    Author(first=" ".join(split_name[:-1]), last=split_name[-1])
                )
        else:
            author = None
        if rets["updated"] is not None:
            year = int(rets["updated"].split("-")[0])
        else:
            year = None

        return Reference(
            author=author,
            title=rets["title"].rstrip(".") if rets["title"] is not None else None,
            journal="arXiv",
            year=year,
            annote=rets["abstract"],
            pages=arxiv,
            doi=f"{self.DOI_PREFIX}{arxiv}",
        )

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""
        if not doi.startswith(self.DOI_PREFIX):
            return None
        return self.from_arxiv(doi[len(self.DOI_PREFIX) :])
