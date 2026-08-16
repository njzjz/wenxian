"""Feeder for PubMed."""

from __future__ import annotations

from typing import ClassVar
from xml.etree import ElementTree

from requests.exceptions import JSONDecodeError

from wenxian import __email__, __tool__
from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION, async_get
from wenxian.reference import Author, Reference


class Pubmed(Feeder):
    """Feeder for PubMed."""

    PMC_IDCONV_URL = "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/"
    ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    EFETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    @staticmethod
    def _pmid_from_pmc_data(data: dict) -> str | None:
        """Extract a PMID from a PMC identifier-conversion response."""
        if data["status"] == "error":
            return None
        records = data["records"]
        if records and "pmid" in records[0]:
            return records[0]["pmid"]
        return None

    def _doi2pmid_pmc(self, doi: str) -> str | None:
        """Convert DOI to PMID using PMC database."""
        r = SESSION.get(
            self.PMC_IDCONV_URL,
            params={"tool": __tool__, "email": __email__, "ids": doi, "format": "json"},
        )
        if r.status_code != 200:
            return None
        try:
            return self._pmid_from_pmc_data(r.json())
        except (JSONDecodeError, KeyError, TypeError):
            return None

    async def _async_doi2pmid_pmc(self, doi: str) -> str | None:
        """Convert DOI to PMID using PMC asynchronously."""
        r = await async_get(
            self.PMC_IDCONV_URL,
            params={"tool": __tool__, "email": __email__, "ids": doi, "format": "json"},
        )
        if r.status_code != 200:
            return None
        try:
            return self._pmid_from_pmc_data(r.json())
        except (KeyError, TypeError, ValueError):
            return None

    @staticmethod
    def _pmid_from_search_data(data: dict) -> str | None:
        """Extract a PMID from a PubMed search response."""
        records = data["esearchresult"]["idlist"]
        return records[0] if records else None

    def _doi2pmid_search(self, doi: str) -> str | None:
        """Convert DOI to PMID using PubMed search."""
        r = SESSION.get(
            self.ESEARCH_URL,
            params={
                "tool": __tool__,
                "email": __email__,
                "db": "pubmed",
                "term": doi,
                "retmode": "json",
                "retmax": "1",
            },
        )
        if r.status_code != 200:
            return None
        try:
            return self._pmid_from_search_data(r.json())
        except (JSONDecodeError, KeyError, TypeError):
            return None

    async def _async_doi2pmid_search(self, doi: str) -> str | None:
        """Convert DOI to PMID using PubMed search asynchronously."""
        r = await async_get(
            self.ESEARCH_URL,
            params={
                "tool": __tool__,
                "email": __email__,
                "db": "pubmed",
                "term": doi,
                "retmode": "json",
                "retmax": "1",
            },
        )
        if r.status_code != 200:
            return None
        try:
            return self._pmid_from_search_data(r.json())
        except (KeyError, TypeError, ValueError):
            return None

    PUBMED_PATH: ClassVar[dict[str, str]] = {
        "author": "PubmedArticle/MedlineCitation/Article/AuthorList/Author",
        "title": "PubmedArticle/MedlineCitation/Article/ArticleTitle",
        "abstract": "PubmedArticle/MedlineCitation/Article/Abstract/AbstractText",
        "journal": "PubmedArticle/MedlineCitation/Article/Journal/Title",
        "volume": "PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/Volume",
        "issue": "PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/Issue",
        "year": "PubmedArticle/MedlineCitation/Article/Journal/JournalIssue/PubDate/Year",
        "pages": "PubmedArticle/MedlineCitation/Article/Pagination/MedlinePgn",
        "doi": "PubmedArticle/PubmedData/ArticleIdList/ArticleId[@IdType='doi']",
        "pii": "PubmedArticle/MedlineCitation/Article/ELocationID[@EIdType='pii']",
    }
    """XPath for PubMed XML."""

    def from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI."""
        pmid = self._doi2pmid_pmc(doi)
        if pmid is None:
            pmid = self._doi2pmid_search(doi)
        if pmid is None:
            return None
        return self._from_pmid(pmid, validate_doi=doi)

    async def async_from_doi(self, doi: str) -> Reference | None:
        """Fetch a reference from a DOI asynchronously."""
        pmid = await self._async_doi2pmid_pmc(doi)
        if pmid is None:
            pmid = await self._async_doi2pmid_search(doi)
        if pmid is None:
            return None
        return await self._async_from_pmid(pmid, validate_doi=doi)

    def from_pmid(self, pmid: str | int) -> Reference | None:
        """Fetch a reference from a PMID."""
        return self._from_pmid(pmid)

    async def async_from_pmid(self, pmid: str | int) -> Reference | None:
        """Fetch a reference from a PMID asynchronously."""
        return await self._async_from_pmid(pmid)

    def _from_content(
        self, content: bytes, validate_doi: str | None = None
    ) -> Reference | None:
        """Convert PubMed XML into a reference."""
        tree = ElementTree.fromstring(content)
        fetched_doi = self._text(tree.find(self.PUBMED_PATH["doi"]))
        if validate_doi is not None and fetched_doi != validate_doi:
            return None
        rets = {}
        for key, path in self.PUBMED_PATH.items():
            if key == "abstract":
                abstract_sections = [
                    self._text(node)
                    for node in tree.findall(self.PUBMED_PATH["abstract"])
                ]
                rets[key] = (
                    " ".join(section for section in abstract_sections if section)
                    or None
                )
            elif key != "author":
                rets[key] = self._text(tree.find(path))

        if rets["journal"] == "Physical chemistry chemical physics : PCCP":
            rets["journal"] = "Physical chemistry chemical physics"

        author = []
        for aa in tree.findall(self.PUBMED_PATH["author"]):
            collective = self._text(aa.find("CollectiveName"))
            if collective is not None:
                author.append(Author(first="", last=collective))
                continue
            first = self._text(aa.find("ForeName"))
            if first is not None:
                first = " ".join(f"{x}." if len(x) == 1 else x for x in first.split())
            author.append(
                Author(
                    first=first,
                    last=self._text(aa.find("LastName")),
                    suffix=self._text(aa.find("Suffix")),
                )
            )
        year = self._int(rets["year"])
        if year is not None:
            assert isinstance(year, int)
        return Reference(
            author=author,
            title=rets["title"].rstrip(".") if rets["title"] is not None else None,
            journal=rets["journal"],
            year=year,
            volume=self._int(rets["volume"]),
            issue=self._int(rets["issue"]),
            pages=self._pages(rets["pages"]) or rets["pii"],
            annote=rets["abstract"],
            doi=fetched_doi,
        )

    def _from_pmid(
        self, pmid: str | int, validate_doi: str | None = None
    ) -> Reference | None:
        r = SESSION.get(
            self.EFETCH_URL,
            params={
                "tool": __tool__,
                "email": __email__,
                "db": "pubmed",
                "id": str(pmid),
                "format": "xml",
            },
        )
        if r.status_code != 200:
            return None
        return self._from_content(r.content, validate_doi)

    async def _async_from_pmid(
        self, pmid: str | int, validate_doi: str | None = None
    ) -> Reference | None:
        r = await async_get(
            self.EFETCH_URL,
            params={
                "tool": __tool__,
                "email": __email__,
                "db": "pubmed",
                "id": str(pmid),
                "format": "xml",
            },
        )
        if r.status_code != 200:
            return None
        return self._from_content(r.content, validate_doi)
