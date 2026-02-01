"""Fetch a reference from an identifier."""

from __future__ import annotations

from difflib import SequenceMatcher

from wenxian.feeder.arxiv import Arxiv
from wenxian.feeder.chemrxiv import Chemrxiv
from wenxian.feeder.crossref import Crossref
from wenxian.feeder.pubmed import Pubmed
from wenxian.feeder.semanticscholar import Semanticscholar
from wenxian.identifier import Identifier, get_identifier_type
from wenxian.logger import logger
from wenxian.reference import Reference


def _title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles (0.0 to 1.0)."""
    # Normalize titles: lowercase and strip whitespace
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    return SequenceMatcher(None, t1, t2).ratio()


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
    Validates that the returned title is similar to the input title.
    """
    # Try to find an identifier from search APIs
    # Use 'or' for lazy evaluation - try Crossref first, then Semantic Scholar
    identifier_info = Crossref().from_title(title) or Semanticscholar().from_title(
        title
    )

    if not identifier_info:
        return Reference()

    identifier_type, identifier_value = identifier_info

    # Fetch metadata using the full feeder chain based on identifier type
    if identifier_type == "PMID":
        result = from_pmid(identifier_value)
    elif identifier_type == "ARXIV":
        result = from_arxiv(identifier_value)
    else:  # DOI
        result = from_doi(identifier_value)

    # Validate that the returned title is similar to the input
    if result and result.title:
        similarity = _title_similarity(title, result.title)
        if similarity < 0.6:  # Threshold for acceptable similarity
            logger.warning(
                f"Title mismatch: input='{title}' vs output='{result.title}' (similarity: {similarity:.2f})"
            )

    return result


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
