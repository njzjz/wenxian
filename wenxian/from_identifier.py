"""Fetch a reference from an identifier."""

from __future__ import annotations

from wenxian.feeder.crossref import Crossref
from wenxian.feeder.pubmed import Pubmed
from wenxian.identifier import Identifier, get_identifier_type
from wenxian.reference import Reference


def from_doi(doi: str) -> Reference | None:
    """Fetch a reference from a DOI."""
    # pubmed is the most reliable source
    return Reference() | Pubmed().from_doi(doi) | Crossref().from_doi(doi)


def from_identifier(identifier: str) -> Reference | None:
    """Fetch a reference from an identifier."""
    identifier_type = get_identifier_type(identifier)
    if identifier_type is None:
        raise ValueError(f"Unknown identifier: {identifier}")
    elif identifier_type == Identifier.DOI:
        return from_doi(identifier)
    elif identifier_type == Identifier.PMID:
        raise NotImplementedError("PMID is not supported yet.")
    elif identifier_type == Identifier.ARXIV:
        raise NotImplementedError("arXiv is not supported yet.")
    else:
        raise RuntimeError("Unknown identifier type.")
