"""Browser-runtime tests for HTTP session setup."""

from __future__ import annotations

import builtins
import runpy
import sys

import pytest

from wenxian.feeder import session


def test_browser_session_skips_native_rate_limiters(monkeypatch):
    """Test importing the browser path never loads native-only limiters."""
    session_path = session.__file__
    assert session_path is not None
    native_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".", maxsplit=1)[0] in {
            "pyrate_limiter",
            "requests_ratelimiter",
        }:
            raise AssertionError(f"browser path imported native package {name}")
        return native_import(name, *args, **kwargs)

    with monkeypatch.context() as browser:
        browser.setattr(sys, "platform", "emscripten")
        browser.setattr(builtins, "__import__", guarded_import)
        namespace = runpy.run_path(session_path)

    with pytest.raises(RuntimeError, match="Synchronous HTTP is unavailable"):
        namespace["SESSION"].get("https://example.test")
