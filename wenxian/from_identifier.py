"""Fetch a reference from an identifier."""

from __future__ import annotations

from wenxian.feeder.arxiv import Arxiv
from wenxian.feeder.chemrxiv import Chemrxiv
from wenxian.feeder.crossref import Crossref
from wenxian.feeder.pubmed import Pubmed
from wenxian.feeder.semanticscholar import Semanticscholar
from wenxian.identifier import Identifier, get_identifier_type
from wenxian.reference import Reference


def from_doi(doi: str) -> Reference | None:
    """Fetch a reference from a DOI."""
    # pubmed is the most reliable source
    return (
        Reference()
        | Pubmed().from_doi(doi)
        | Crossref().from_doi(doi)
        | Arxiv().from_doi(doi)
        | Chemrxiv().from_doi(doi)
        | Semanticscholar().from_doi(doi)
    )


def from_pmid(pmid: str | int) -> Reference | None:
    """Fetch a reference from a PMID."""
    # no need to fetch from crossref - pubmed usually has all information
    return Reference() | Pubmed().from_pmid(pmid)


def from_arxiv(arxiv: str) -> Reference | None:
    """Fetch a reference from an arXiv identifier."""
    # arxiv api has all information for arxiv papers
    return Reference() | Arxiv().from_arxiv(arxiv)


def from_title(title: str) -> Reference | None:
    """Search and fetch a reference from a title."""
    # Try multiple sources for best results
    return (
        Reference()
        | Crossref().from_title(title)
        | Semanticscholar().from_title(title)
    )


def from_identifier(identifier: str) -> Reference | None:
    """Fetch a reference from an identifier or title."""
    identifier_type = get_identifier_type(identifier)
    if identifier_type == Identifier.DOI:
        return from_doi(identifier)
    elif identifier_type == Identifier.PMID:
        return from_pmid(identifier)
    elif identifier_type == Identifier.ARXIV:
        return from_arxiv(identifier)
    else:
        # Fallback to title search for unknown identifiers
        return from_title(identifier)
