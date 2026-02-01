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
    """Fetch a reference from a title.

    Searches for the paper using Crossref and Semantic Scholar,
    extracts the identifier (DOI/PMID/arXiv), and then fetches
    metadata from multiple sources for the best quality data.
    """
    # Try to find an identifier from search APIs
    identifier = None

    # Try Crossref first
    crossref_result = Crossref().from_title(title)
    if crossref_result:
        identifier = crossref_result
    else:
        # Fall back to Semantic Scholar
        ss_result = Semanticscholar().from_title(title)
        if ss_result:
            identifier = ss_result

    if not identifier:
        return Reference()

    # Now fetch metadata using the full feeder chain based on identifier type
    if identifier.startswith("PMID:"):
        pmid = identifier[5:]  # Remove "PMID:" prefix
        return from_pmid(pmid)
    elif identifier.startswith("ARXIV:"):
        arxiv_id = identifier[6:]  # Remove "ARXIV:" prefix
        return from_arxiv(arxiv_id)
    else:
        # Assume it's a DOI
        return from_doi(identifier)


def from_identifier(identifier: str) -> Reference | None:
    """Fetch a reference from an identifier."""
    identifier_type = get_identifier_type(identifier)
    if identifier_type is None:
        raise ValueError(f"Unknown identifier: {identifier}")
    elif identifier_type == Identifier.DOI:
        return from_doi(identifier)
    elif identifier_type == Identifier.PMID:
        return from_pmid(identifier)
    elif identifier_type == Identifier.ARXIV:
        return from_arxiv(identifier)
    elif identifier_type == Identifier.TITLE:
        return from_title(identifier)
    else:
        raise RuntimeError("Unknown identifier type.")
