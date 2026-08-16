"""Tests for native request timeout defaults."""

from __future__ import annotations

from wenxian.feeder import session


class _Response:
    """Minimal response returned by the patched requests session."""


def test_native_session_applies_default_timeout(monkeypatch):
    """Test native requests get a bounded timeout unless explicitly overridden."""
    calls = []

    def fake_request(self, method, url, **kwargs):
        calls.append((method, url, kwargs))
        return _Response()

    monkeypatch.setattr(session.Session, "request", fake_request)

    session.SESSION.get("https://example.test")
    session.SESSION.get("https://example.test", timeout=1.5)

    assert calls[0][2]["timeout"] == session._DEFAULT_TIMEOUT
    assert calls[1][2]["timeout"] == 1.5
