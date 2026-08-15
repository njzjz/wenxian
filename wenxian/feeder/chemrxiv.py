"""Feeder for ChemRxiv."""

from __future__ import annotations

import sys
from datetime import datetime

from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION, async_get
from wenxian.reference import Author, Reference


class Chemrxiv(Feeder):
    """Feeder for ChemRxiv."""

    DOI_PREFIX = "10.26434/chemrxiv"
    """DOI prefix for ChemRxiv."""
    API_URL = "https://chemrxiv.org/engage/chemrxiv/public-api/v1/items/doi"

    @staticmethod
    def _from_data(data: dict, doi: str) -> Reference:
        """Convert ChemRxiv metadata into a reference."""
        publish_time_str = data["publishedDate"]
        if sys.version_info < (3, 11) and publish_time_str.endswith("Z"):
            publish_time_str = publish_time_str[:-1] + "+00:00"
        publish_time = datetime.fromisoformat(publish_time_str)
        authors = [
            Author(first=item["firstName"], last=item["lastName"])
            for item in data["authors"]
        ]
        return Reference(
            author=authors,
            title=data["title"],
            journal="ChemRxiv",
            year=publish_time.year,
            annote=data["abstract"],
            doi=doi,
        )

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""
        if not doi.startswith(self.DOI_PREFIX):
            return None
        r = SESSION.get(f"{self.API_URL}/{doi}")
        if r.status_code == 404:
            return None
        return self._from_data(r.json(), doi)

    async def async_from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI asynchronously."""
        if not doi.startswith(self.DOI_PREFIX):
            return None
        r = await async_get(f"{self.API_URL}/{doi}")
        if r.status_code == 404:
            return None
        return self._from_data(r.json(), doi)
