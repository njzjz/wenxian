"""Fetch a reference from an identifier."""

from __future__ import annotations

import sys
from difflib import SequenceMatcher
from typing import Any, Callable, TypeVar

from requests.exceptions import RequestException

from wenxian.feeder.arxiv import Arxiv
from wenxian.feeder.chemrxiv import Chemrxiv
from wenxian.feeder.crossref import Crossref
from wenxian.feeder.datacite import Datacite
from wenxian.feeder.europepmc import Europepmc
from wenxian.feeder.pubmed import Pubmed
from wenxian.feeder.semanticscholar import Semanticscholar
from wenxian.identifier import Identifier, get_identifier_type
from wenxian.logger import logger
from wenxian.reference import Reference

T = TypeVar("T")


def _title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles (0.0 to 1.0)."""
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    return SequenceMatcher(None, t1, t2).ratio()


def _fetch_safely(
    source: str, fetcher: Callable[[Any], T | None], identifier: Any
) -> T | None:
    """Fetch from one source without aborting a browser fallback chain."""
    try:
        return fetcher(identifier)
    except (OSError, RequestException) as exc:
        logger.warning("%s lookup failed for %s: %s", source, identifier, exc)
        return None
    except Exception as exc:
        # Browser networking can surface JavaScript exceptions that are not
        # requests exceptions. Keep native Python strict so programming errors
        # remain visible during normal use and tests.
        if sys.platform != "emscripten":
            raise
        logger.warning("%s browser lookup failed for %s: %s", source, identifier, exc)
        return None


def from_doi(doi: str) -> Reference | None:
    """Fetch a reference from a DOI."""
    return (
        Reference()
        | _fetch_safely("PubMed", Pubmed().from_doi, doi)
        | _fetch_safely("Crossref", Crossref().from_doi, doi)
        | _fetch_safely("arXiv", Arxiv().from_doi, doi)
        | _fetch_safely("ChemRxiv", Chemrxiv().from_doi, doi)
        | _fetch_safely("Semantic Scholar", Semanticscholar().from_doi, doi)
    )


def from_pmid(pmid: str | int) -> Reference | None:
    """Fetch a reference from a PMID."""
    reference = _fetch_safely("PubMed", Pubmed().from_pmid, pmid)
    if reference is not None and not reference.is_empty():
        return reference
    return (
        Reference()
        | _fetch_safely("Europe PMC", Europepmc().from_pmid, pmid)
        | _fetch_safely("Semantic Scholar", Semanticscholar().from_pmid, pmid)
    )


def from_arxiv(arxiv: str) -> Reference | None:
    """Fetch a reference from an arXiv identifier."""
    reference = _fetch_safely("arXiv", Arxiv().from_arxiv, arxiv)
    if reference is not None and not reference.is_empty():
        return reference
    return (
        Reference()
        | _fetch_safely("DataCite", Datacite().from_arxiv, arxiv)
        | _fetch_safely("Semantic Scholar", Semanticscholar().from_arxiv, arxiv)
    )


def from_title(title: str) -> Reference | None:
    """Fetch a reference from a title.

    Searches for the paper using Crossref and Semantic Scholar,
    extracts the identifier (DOI/PMID/arXiv), and then fetches
    metadata from multiple sources for the best quality data.
    Validates that the returned title is similar to the input title.
    """
    identifier_info = _fetch_safely("Crossref", Crossref().from_title, title)
    if identifier_info is None:
        identifier_info = _fetch_safely(
            "Semantic Scholar", Semanticscholar().from_title, title
        )
    if identifier_info is None:
        return None
    assert isinstance(identifier_info, str)

    result = from_identifier(identifier_info)

    if result and result.title:
        similarity = _title_similarity(title, result.title)
        if similarity < 0.6:
            logger.warning(
                f"Title mismatch: input='{title}' vs output='{result.title}' (similarity: {similarity:.2f})"
            )
            return None

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
