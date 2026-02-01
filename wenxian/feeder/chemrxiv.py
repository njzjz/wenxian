"""Feeder for arXiv."""

from __future__ import annotations

import sys
from datetime import datetime

from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION
from wenxian.reference import Author, Reference


class Chemrxiv(Feeder):
    """Feeder for ChemRxiv."""

    DOI_PREFIX = "10.26434/chemrxiv"
    """DOI prefix for ChemRxiv."""

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""
        if not doi.startswith(self.DOI_PREFIX):
            return None
        # https://chemrxiv.org/engage/chemrxiv/public-api/v1/items/doi/10.26434/chemrxiv-2024-sq8nh
        r = SESSION.get(
            f"https://chemrxiv.org/engage/chemrxiv/public-api/v1/items/doi/{doi}",
        )
        if r.status_code == 404:
            # DOI not found
            return None
        res = r.json()
        publish_time_str = res["publishedDate"]
        if sys.version_info < (3, 11) and publish_time_str.endswith("Z"):
            # Z support added in https://github.com/python/cpython/issues/80010
            publish_time_str = publish_time_str[:-1] + "+00:00"
        publish_time = datetime.fromisoformat(publish_time_str)
        year = publish_time.year
        authors = []
        for aa in res["authors"]:
            authors.append(Author(first=aa["firstName"], last=aa["lastName"]))
        return Reference(
            author=authors,
            title=res["title"],
            journal="ChemRxiv",
            year=year,
            annote=res["abstract"],
            doi=doi,
        )
