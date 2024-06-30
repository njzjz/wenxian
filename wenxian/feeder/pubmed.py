"""Feeder for PubMed."""

from __future__ import annotations

from typing import ClassVar
from xml.etree import ElementTree

from wenxian import __email__, __tool__
from wenxian.feeder.feeder import Feeder
from wenxian.feeder.session import SESSION
from wenxian.reference import Author, Reference


class Pubmed(Feeder):
    """Feeder for PubMed."""

    def _doi2pmid_pmc(self, doi: str) -> str | None:
        """Convert DOI to PMID using PMC database.

        Parameters
        ----------
        doi : str
            A DOI string.

        Returns
        -------
        str | None
            A PMID string if found or None if not found.
        """
        r = SESSION.get(
            "https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
            params={"tool": __tool__, "email": __email__, "ids": doi, "format": "json"},
        )
        res = r.json()
        if res["status"] == "error":
            return None
        records = res["records"]

        if records and "pmid" in records[0]:
            return records[0]["pmid"]
        return None

    def _doi2pmid_search(self, doi: str) -> str | None:
        """Convert DOI to PMID using PubMed search.

        The returned PMID may be incorrect if the reference is not in the
        database. Need to validate it.

        Parameters
        ----------
        doi : str
            A DOI string.

        Returns
        -------
        str | None
            A PMID string if found or None if not found.
        """
        r = SESSION.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={
                "tool": __tool__,
                "email": __email__,
                "db": "pubmed",
                "term": doi,
                "retmode": "json",
                "retmax": "1",
            },
        )
        records = r.json()["esearchresult"]["idlist"]

        if records:
            return records[0]
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
        # get PMID. PMC is more reliable than search
        pmid = self._doi2pmid_pmc(doi)
        if pmid is None:
            pmid = self._doi2pmid_search(doi)
        if pmid is None:
            # not found
            return None
        return self._from_pmid(pmid, validate_doi=doi)

    def from_pmid(self, pmid: str | int) -> Reference | None:
        """Fetch a reference from a PMID."""
        return self._from_pmid(pmid)

    def _from_pmid(
        self, pmid: str | int, validate_doi: str | None = None
    ) -> Reference | None:
        r = SESSION.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={
                "tool": __tool__,
                "email": __email__,
                "db": "pubmed",
                "id": str(pmid),
                "format": "xml",
            },
        )
        tree = ElementTree.fromstring(r.content)
        fetched_doi = self._text(tree.find(self.PUBMED_PATH["doi"]))
        if validate_doi is not None and fetched_doi != validate_doi:
            # DOI not match, ignore
            return None
        rets = {}
        for key, path in self.PUBMED_PATH.items():
            if key not in ("author",):
                rets[key] = self._text(tree.find(path))

        # specially handle Physical chemistry chemical physics : PCCP
        # DOI: 10.1039/d4cp00997e
        if rets["journal"] == "Physical chemistry chemical physics : PCCP":
            rets["journal"] = "Physical chemistry chemical physics"

        author_tree = tree.findall(self.PUBMED_PATH["author"])
        if author_tree is not None:
            author = []
            for aa in author_tree:
                first = self._text(aa.find("ForeName"))
                if first is not None:
                    # add period if it is a single letter, e.g., Darrin M -> Darrin M.
                    first = " ".join(
                        f"{x}." if len(x) == 1 else x for x in first.split()
                    )
                author.append(
                    Author(
                        first=first,
                        last=self._text(aa.find("LastName")),
                        suffix=self._text(aa.find("Suffix")),
                    )
                )
        else:
            author = None
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
