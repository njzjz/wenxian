"""Fetch a reference from an identifier."""

from __future__ import annotations

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from typing import TYPE_CHECKING, TypeVar
from xml.etree.ElementTree import ParseError

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

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Iterable

T = TypeVar("T")
_SOURCE_DATA_ERRORS = (KeyError, IndexError, TypeError, ValueError, ParseError)


def _title_similarity(title1: str, title2: str) -> float:
    """Calculate similarity between two titles (0.0 to 1.0)."""
    t1 = title1.lower().strip()
    t2 = title2.lower().strip()
    return SequenceMatcher(None, t1, t2).ratio()


def _fetch_safely(
    source: str, fetcher: Callable[..., T | None], identifier: object
) -> T | None:
    """Fetch from one source without aborting a fallback chain."""
    try:
        return fetcher(identifier)
    except (OSError, RequestException, *_SOURCE_DATA_ERRORS) as exc:
        logger.warning("%s lookup failed for %s: %s", source, identifier, exc)
        return None
    except Exception as exc:
        if sys.platform != "emscripten":
            raise
        logger.warning("%s browser lookup failed for %s: %s", source, identifier, exc)
        return None


async def _async_fetch_safely(
    source: str,
    fetcher: Callable[..., Awaitable[T | None]],
    identifier: object,
) -> T | None:
    """Fetch from one source asynchronously without aborting other sources."""
    try:
        return await fetcher(identifier)
    except (OSError, RequestException, *_SOURCE_DATA_ERRORS) as exc:
        logger.warning("%s lookup failed for %s: %s", source, identifier, exc)
        return None
    except Exception as exc:
        if sys.platform != "emscripten":
            raise
        logger.warning("%s browser lookup failed for %s: %s", source, identifier, exc)
        return None


def _fetch_references_concurrently(
    fetches: Iterable[tuple[str, Callable[..., Reference | None], str | int]],
) -> list[Reference | None]:
    """Run independent synchronous reference lookups concurrently."""
    fetches = tuple(fetches)
    if sys.platform == "emscripten":
        return [
            _fetch_safely(source, fetcher, identifier)
            for source, fetcher, identifier in fetches
        ]
    with ThreadPoolExecutor(max_workers=len(fetches)) as executor:
        futures = [
            executor.submit(_fetch_safely, source, fetcher, identifier)
            for source, fetcher, identifier in fetches
        ]
        return [future.result() for future in futures]


def _merge_references(references: Iterable[Reference | None]) -> Reference:
    """Merge source results in their configured priority order."""
    result = Reference()
    for reference in references:
        result = result | reference
    return result


def from_doi(doi: str) -> Reference | None:
    """Fetch a reference from DOI sources concurrently."""
    return _merge_references(
        _fetch_references_concurrently(
            (
                ("PubMed", Pubmed().from_doi, doi),
                ("Crossref", Crossref().from_doi, doi),
                ("arXiv", Arxiv().from_doi, doi),
                ("ChemRxiv", Chemrxiv().from_doi, doi),
                ("Semantic Scholar", Semanticscholar().from_doi, doi),
            )
        )
    )


async def async_from_doi(doi: str) -> Reference | None:
    """Fetch a reference from DOI sources concurrently."""
    references = await asyncio.gather(
        _async_fetch_safely("PubMed", Pubmed().async_from_doi, doi),
        _async_fetch_safely("Crossref", Crossref().async_from_doi, doi),
        _async_fetch_safely("arXiv", Arxiv().async_from_doi, doi),
        _async_fetch_safely("ChemRxiv", Chemrxiv().async_from_doi, doi),
        _async_fetch_safely("Semantic Scholar", Semanticscholar().async_from_doi, doi),
    )
    return _merge_references(references)


def from_pmid(pmid: str | int) -> Reference | None:
    """Fetch a reference from a PMID."""
    reference = _fetch_safely("PubMed", Pubmed().from_pmid, pmid)
    if reference is not None and not reference.is_empty():
        return reference
    return _merge_references(
        _fetch_references_concurrently(
            (
                ("Europe PMC", Europepmc().from_pmid, pmid),
                ("Semantic Scholar", Semanticscholar().from_pmid, pmid),
            )
        )
    )


async def async_from_pmid(pmid: str | int) -> Reference | None:
    """Fetch a reference from a PMID without blocking the event loop."""
    reference = await _async_fetch_safely("PubMed", Pubmed().async_from_pmid, pmid)
    if reference is not None and not reference.is_empty():
        return reference
    fallbacks = await asyncio.gather(
        _async_fetch_safely("Europe PMC", Europepmc().async_from_pmid, pmid),
        _async_fetch_safely(
            "Semantic Scholar", Semanticscholar().async_from_pmid, pmid
        ),
    )
    return _merge_references(fallbacks)


def from_arxiv(arxiv: str) -> Reference | None:
    """Fetch a reference from an arXiv identifier."""
    reference = _fetch_safely("arXiv", Arxiv().from_arxiv, arxiv)
    if reference is not None and not reference.is_empty():
        return reference
    return _merge_references(
        _fetch_references_concurrently(
            (
                ("DataCite", Datacite().from_arxiv, arxiv),
                ("Semantic Scholar", Semanticscholar().from_arxiv, arxiv),
            )
        )
    )


async def async_from_arxiv(arxiv: str) -> Reference | None:
    """Fetch an arXiv reference without blocking the event loop."""
    reference = await _async_fetch_safely("arXiv", Arxiv().async_from_arxiv, arxiv)
    if reference is not None and not reference.is_empty():
        return reference
    fallbacks = await asyncio.gather(
        _async_fetch_safely("DataCite", Datacite().async_from_arxiv, arxiv),
        _async_fetch_safely(
            "Semantic Scholar", Semanticscholar().async_from_arxiv, arxiv
        ),
    )
    return _merge_references(fallbacks)


def _validate_title_result(title: str, result: Reference | None) -> Reference | None:
    """Reject a title-search result that is too dissimilar to the query."""
    if result and result.title:
        similarity = _title_similarity(title, result.title)
        if similarity < 0.6:
            logger.warning(
                f"Title mismatch: input='{title}' vs output='{result.title}' (similarity: {similarity:.2f})"
            )
            return None
    return result


def from_title(title: str) -> Reference | None:
    """Fetch a reference from a title."""
    identifier_info = _fetch_safely("Crossref", Crossref().from_title, title)
    if identifier_info is None:
        identifier_info = _fetch_safely(
            "Semantic Scholar", Semanticscholar().from_title, title
        )
    if identifier_info is None:
        return None
    assert isinstance(identifier_info, str)
    return _validate_title_result(title, from_identifier(identifier_info))


async def async_from_title(title: str) -> Reference | None:
    """Fetch a reference from a title without blocking the event loop."""
    identifier_info = await _async_fetch_safely(
        "Crossref", Crossref().async_from_title, title
    )
    if identifier_info is None:
        identifier_info = await _async_fetch_safely(
            "Semantic Scholar", Semanticscholar().async_from_title, title
        )
    if identifier_info is None:
        return None
    assert isinstance(identifier_info, str)
    return _validate_title_result(title, await async_from_identifier(identifier_info))


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


async def async_from_identifier(identifier: str) -> Reference | None:
    """Fetch a reference from an identifier asynchronously."""
    identifier_type = get_identifier_type(identifier)
    if identifier_type is None:
        raise ValueError(f"Unknown identifier: {identifier}")
    elif identifier_type == Identifier.DOI:
        return await async_from_doi(identifier)
    elif identifier_type == Identifier.PMID:
        return await async_from_pmid(identifier)
    elif identifier_type == Identifier.ARXIV:
        return await async_from_arxiv(identifier)
    elif identifier_type == Identifier.TITLE:
        return await async_from_title(identifier)
    else:
        raise RuntimeError("Unknown identifier type.")
