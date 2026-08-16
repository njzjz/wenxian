"""Requests session with synchronous and asynchronous transports."""

from __future__ import annotations

import asyncio
import json
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING
from urllib.parse import urlencode

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop
    from collections.abc import Mapping
    from typing import Any

if sys.platform != "emscripten":
    from pyrate_limiter import Duration, Limiter, Rate
    from requests import Session
    from requests.adapters import HTTPAdapter, Retry
    from requests_ratelimiter import LimiterAdapter
    from requests_ratelimiter.requests_ratelimiter import HostBucketFactory


@dataclass
class _BrowserResponse:
    """Requests-compatible response returned by the browser Fetch API."""

    status_code: int
    content: bytes

    def json(self) -> Any:
        """Decode the response body as JSON."""
        return json.loads(self.content)


@dataclass
class _SpacingState:
    """Per-event-loop state for a browser request limiter."""

    lock: asyncio.Lock
    next_start: float = 0.0


class _AsyncSpacingLimiter:
    """Space browser requests to one service without blocking the event loop."""

    def __init__(self, interval: float) -> None:
        self.interval = interval
        self._states: dict[AbstractEventLoop, _SpacingState] = {}

    async def wait(self) -> None:
        """Wait until the next request may start."""
        loop = asyncio.get_running_loop()
        state = self._states.get(loop)
        if state is None:
            state = _SpacingState(asyncio.Lock())
            self._states[loop] = state

        async with state.lock:
            delay = state.next_start - loop.time()
            if delay > 0:
                await asyncio.sleep(delay)
            state.next_start = loop.time() + self.interval


class _BrowserSession:
    """Reject synchronous HTTP calls in browser runtimes."""

    def get(self, *args: Any, **kwargs: Any) -> Any:
        """Raise because Pyodide networking must use the asynchronous transport."""
        raise RuntimeError(
            "Synchronous HTTP is unavailable in Pyodide; use async_get instead."
        )


if sys.platform != "emscripten":
    _DEFAULT_TIMEOUT = (5.0, 20.0)

    class _TimeoutSession(Session):
        """Requests session that applies a bounded timeout by default."""

        def request(self, method, url, **kwargs):
            """Send a request with the shared default timeout unless overridden."""
            kwargs.setdefault("timeout", _DEFAULT_TIMEOUT)
            return super().request(method, url, **kwargs)

    SESSION = _TimeoutSession()

    # retry logic
    retries = Retry(
        total=5,
        backoff_factor=0.1,
        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],
    )

    adapter_ncbi = LimiterAdapter(per_second=3, max_retries=retries)
    SESSION.mount("https://www.ncbi.nlm.nih.gov/pmc/utils/", adapter_ncbi)
    SESSION.mount("https://eutils.ncbi.nlm.nih.gov/", adapter_ncbi)
    adapter_crossref = LimiterAdapter(per_second=50, max_retries=retries)
    SESSION.mount("https://api.crossref.org/", adapter_crossref)
    adapter_arxiv = LimiterAdapter(
        limiter=Limiter(HostBucketFactory([Rate(1, Duration.SECOND * 3)])),
        burst=1,
        max_retries=retries,
    )
    SESSION.mount("https://export.arxiv.org/api", adapter_arxiv)
    adapter_semanticscholar = LimiterAdapter(per_second=1, max_retries=retries)
    SESSION.mount("https://api.semanticscholar.org/", adapter_semanticscholar)
    SESSION.mount("https://", HTTPAdapter(max_retries=retries))
else:
    SESSION = _BrowserSession()


_BROWSER_RETRY_STATUSES = {429, 500, 502, 503, 504}
_BROWSER_TIMEOUT = 20.0
_BROWSER_RETRIES = 2
_BROWSER_BACKOFF = 0.1
_BROWSER_NCBI_LIMITER = _AsyncSpacingLimiter(1 / 3)
_BROWSER_LIMITERS = (
    ("https://www.ncbi.nlm.nih.gov/pmc/utils/", _BROWSER_NCBI_LIMITER),
    ("https://eutils.ncbi.nlm.nih.gov/", _BROWSER_NCBI_LIMITER),
    ("https://api.crossref.org/", _AsyncSpacingLimiter(1 / 50)),
    ("https://export.arxiv.org/api", _AsyncSpacingLimiter(3)),
    ("https://api.semanticscholar.org/", _AsyncSpacingLimiter(1)),
)


def _url_with_params(url: str, params: Mapping[str, str | int] | None) -> str:
    """Append query parameters to a URL."""
    if not params:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}{urlencode(params)}"


def _browser_limiter_for(url: str) -> _AsyncSpacingLimiter | None:
    """Return the configured browser-side limiter for a URL."""
    for prefix, limiter in _BROWSER_LIMITERS:
        if url.startswith(prefix):
            return limiter
    return None


async def _browser_get(
    url: str, params: Mapping[str, str | int] | None
) -> _BrowserResponse:
    """Perform one asynchronous browser request."""
    from pyodide.http import pyfetch  # type: ignore[import-not-found]

    async def fetch_and_read() -> _BrowserResponse:
        response = await pyfetch(_url_with_params(url, params), method="GET")
        return _BrowserResponse(response.status, await response.bytes())

    return await asyncio.wait_for(fetch_and_read(), timeout=_BROWSER_TIMEOUT)


async def async_get(url: str, *, params: Mapping[str, str | int] | None = None) -> Any:
    """Perform a GET request without blocking the active event loop.

    Native Python runs the existing rate-limited requests session in a worker
    thread. Pyodide cannot start threads, so it uses ``pyfetch`` instead.
    """
    if sys.platform != "emscripten":
        return await asyncio.to_thread(SESSION.get, url, params=params)

    limiter = _browser_limiter_for(url)
    response: _BrowserResponse | None = None
    for attempt in range(_BROWSER_RETRIES + 1):
        if limiter is not None:
            await limiter.wait()
        response = await _browser_get(url, params)
        if response.status_code not in _BROWSER_RETRY_STATUSES:
            return response
        if attempt < _BROWSER_RETRIES:
            await asyncio.sleep(_BROWSER_BACKOFF * (2**attempt))

    assert response is not None
    return response


__all__ = ["SESSION", "async_get"]
