"""Requests session with rate limiting."""

from __future__ import annotations

from requests import Session
from requests_ratelimiter import LimiterAdapter

SESSION = Session()
# https://www.ncbi.nlm.nih.gov/books/NBK25497/
adapter_ncbi = LimiterAdapter(per_second=3)
SESSION.mount("https://www.ncbi.nlm.nih.gov/pmc/utils/", adapter_ncbi)
SESSION.mount("https://eutils.ncbi.nlm.nih.gov/", adapter_ncbi)
# Crossref rate limit is not documented but discussed in
# https://github.com/CrossRef/rest-api-doc/issues/196
adapter_crossref = LimiterAdapter(per_second=50)
SESSION.mount("https://api.crossref.org/", adapter_crossref)

__all__ = ["SESSION"]
