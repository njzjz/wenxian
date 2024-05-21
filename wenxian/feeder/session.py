"""Requests session with rate limiting."""

from __future__ import annotations

from pyrate_limiter import Duration, Limiter, RequestRate
from requests import Session
from requests.adapters import HTTPAdapter, Retry
from requests_ratelimiter import LimiterAdapter

SESSION = Session()

# retry logic
retries = Retry(
    total=5,
    backoff_factor=0.1,
    status_forcelist=[
        429,  # Too Many Requests
        500,  # Internal Server Error
        502,  # bad gateway server error
        503,  # the server is currently unable to handle the incoming requests
        504,  # Gateway Timeout
    ],
)

# https://www.ncbi.nlm.nih.gov/books/NBK25497/
adapter_ncbi = LimiterAdapter(per_second=3, max_retries=retries)
SESSION.mount("https://www.ncbi.nlm.nih.gov/pmc/utils/", adapter_ncbi)
SESSION.mount("https://eutils.ncbi.nlm.nih.gov/", adapter_ncbi)
# Crossref rate limit is not documented but discussed in
# https://github.com/CrossRef/rest-api-doc/issues/196
adapter_crossref = LimiterAdapter(per_second=50, max_retries=retries)
SESSION.mount("https://api.crossref.org/", adapter_crossref)
# Arxiv: https://info.arxiv.org/help/api/tou.html
adapter_arxiv = LimiterAdapter(
    limiter=Limiter(RequestRate(1, Duration.SECOND * 3)), burst=1, max_retries=retries
)
SESSION.mount("https://export.arxiv.org/api", adapter_arxiv)
# https://www.semanticscholar.org/product/api
adapter_semanticscholar = LimiterAdapter(per_second=1, max_retries=retries)
SESSION.mount("https://api.semanticscholar.org/", adapter_semanticscholar)

SESSION.mount("https://", HTTPAdapter(max_retries=retries))

__all__ = ["SESSION"]
