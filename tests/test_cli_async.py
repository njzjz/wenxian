"""Tests for asynchronous CLI behavior."""

from __future__ import annotations

import asyncio

import pytest

from wenxian import __main__ as cli


class _Reference:
    """Minimal reference object for CLI tests."""

    def __init__(self, value: str) -> None:
        self.bibtex = value
        self.markdown = value
        self.text = value
        self.key = value

    def is_empty(self) -> bool:
        """Return whether the reference is empty."""
        return False


def test_cmd_from_uses_async_fetches_concurrently(monkeypatch, capsys):
    """Test concurrent async lookups with deterministic output order."""
    started = 0
    all_started = None

    async def fake_from_identifier(identifier):
        nonlocal all_started, started
        if all_started is None:
            all_started = asyncio.Event()
        started += 1
        if started == 2:
            all_started.set()
        await asyncio.wait_for(all_started.wait(), timeout=1)
        return _Reference(identifier)

    monkeypatch.setattr(cli, "async_from_identifier", fake_from_identifier)
    cli.cmd_from(IDENTIFIER=[" first ", "second"], output_type="text")

    assert capsys.readouterr().out == "first\nsecond"


def test_cmd_from_preserves_async_error_handling(monkeypatch, capsys):
    """Test ignored async failures do not discard successful references."""

    async def fake_from_identifier(identifier):
        if identifier == "bad":
            raise RuntimeError("boom")
        return _Reference(identifier)

    monkeypatch.setattr(cli, "async_from_identifier", fake_from_identifier)
    cli.cmd_from(
        IDENTIFIER=["bad", "good"],
        ignore_errors=True,
        output_type="text",
    )

    assert capsys.readouterr().out == "good"


def test_cmd_from_wraps_async_error(monkeypatch):
    """Test non-ignored async failures retain identifier context."""

    async def fake_from_identifier(identifier):
        raise RuntimeError("boom")

    monkeypatch.setattr(cli, "async_from_identifier", fake_from_identifier)
    with pytest.raises(ValueError, match="Failed to fetch reference from bad: boom"):
        cli.cmd_from(IDENTIFIER=["bad"])
