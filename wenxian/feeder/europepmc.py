"""Feeder for the Europe PMC API."""

from __future__ import annotations

from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION
from wenxian.reference import Author, Reference


class Europepmc(Feeder):
    """Feeder for the Europe PMC API."""

    API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

    def from_pmid(self, pmid: str | int) -> Reference | None:
        """Fetch a reference from a PubMed identifier."""
        r = SESSION.get(
            self.API_URL,
            params={
                "query": f"EXT_ID:{pmid} AND SRC:MED",
                "resultType": "core",
                "format": "json",
                "pageSize": "1",
            },
        )
        if r.status_code != 200:
            return None

        results = r.json().get("resultList", {}).get("result", [])
        if not results:
            return None
        return self._from_result(results[0])

    def _from_result(self, result: dict) -> Reference:
        """Convert a Europe PMC result into a reference."""
        authors = []
        for item in result.get("authorList", {}).get("author", []):
            first = item.get("firstName")
            last = item.get("lastName")
            if last is None and item.get("fullName"):
                parts = item["fullName"].split()
                first = " ".join(parts[:-1])
                last = parts[-1]
            if first is not None and last is not None:
                authors.append(Author(first=first, last=last))

        journal_info = result.get("journalInfo") or {}
        journal_data = journal_info.get("journal") or {}
        journal = journal_data.get("title") or result.get("journalTitle")

        return Reference(
            author=authors or None,
            title=result.get("title"),
            journal=journal,
            year=self._int(result.get("pubYear")),
            volume=self._int(journal_info.get("volume")),
            issue=self._int(journal_info.get("issue")),
            pages=self._pages(result.get("pageInfo")),
            annote=result.get("abstractText"),
            doi=result.get("doi"),
        )
