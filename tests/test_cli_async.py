"""Tests for asynchronous CLI behavior."""

from __future__ import annotations

import asyncio
import sys

import pytest

from wenxian import __main__ as cli


class _Reference:
    """Minimal reference object for CLI tests."""

    def __init__(self, value: str, *, empty: bool = False) -> None:
        self.bibtex = value
        self.markdown = value
        self.text = value
        self.key = value
        self._empty = empty

    def is_empty(self) -> bool:
        """Return whether the reference is empty."""
        return self._empty


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


def test_cmd_from_wraps_async_error_and_cancels_pending(monkeypatch):
    """Test non-ignored failures cancel later lookups and retain context."""
    slow_started = None
    cancelled = False

    async def fake_from_identifier(identifier):
        nonlocal cancelled, slow_started
        if slow_started is None:
            slow_started = asyncio.Event()
        if identifier == "bad":
            await slow_started.wait()
            raise RuntimeError("boom")
        slow_started.set()
        try:
            await asyncio.Future()
        except asyncio.CancelledError:
            cancelled = True
            raise

    monkeypatch.setattr(cli, "async_from_identifier", fake_from_identifier)
    with pytest.raises(ValueError, match="Failed to fetch reference from bad: boom"):
        cli.cmd_from(IDENTIFIER=["bad", "slow"])

    assert cancelled


@pytest.mark.parametrize(
    ("output_type", "extension"),
    [("bibtex", ".bib"), ("markdown", ".md"), ("text", ".txt")],
)
def test_cmd_from_writes_default_single_file(
    monkeypatch, tmp_path, output_type, extension
):
    """Test default output names for every supported format."""

    async def fake_from_identifier(identifier):
        return _Reference(identifier)

    monkeypatch.setattr(cli, "async_from_identifier", fake_from_identifier)
    monkeypatch.chdir(tmp_path)
    cli.cmd_from(IDENTIFIER=["item"], output=0, output_type=output_type)

    assert (tmp_path / f"item{extension}").read_text() == "item"


def test_cmd_from_writes_default_multiple_file(monkeypatch, tmp_path):
    """Test the shared filename used for multiple references."""

    async def fake_from_identifier(identifier):
        return _Reference(identifier)

    monkeypatch.setattr(cli, "async_from_identifier", fake_from_identifier)
    monkeypatch.chdir(tmp_path)
    cli.cmd_from(IDENTIFIER=["one", "two"], output=0)

    assert (tmp_path / "references.bib").read_text() == "one\ntwo"


def test_cmd_from_writes_explicit_file(monkeypatch, tmp_path):
    """Test writing references to an explicit output path."""

    async def fake_from_identifier(identifier):
        return _Reference(identifier)

    output = tmp_path / "output.bib"
    monkeypatch.setattr(cli, "async_from_identifier", fake_from_identifier)
    cli.cmd_from(IDENTIFIER=["item"], output=str(output))

    assert output.read_text() == "item"


@pytest.mark.parametrize("result", [None, _Reference("empty", empty=True)])
def test_cmd_from_rejects_empty_reference(monkeypatch, result):
    """Test empty lookup results fail unless errors are ignored."""

    async def fake_from_identifier(identifier):
        return result

    monkeypatch.setattr(cli, "async_from_identifier", fake_from_identifier)
    with pytest.raises(ValueError, match="Failed to fetch reference from missing"):
        cli.cmd_from(IDENTIFIER=["missing"])


def test_cmd_from_ignores_empty_reference(monkeypatch, capsys):
    """Test ignored empty results produce no output."""
    errors = []

    async def fake_from_identifier(identifier):
        return None

    monkeypatch.setattr(cli, "async_from_identifier", fake_from_identifier)
    monkeypatch.setattr(cli.logger, "error", errors.append)
    cli.cmd_from(IDENTIFIER=["missing"], ignore_errors=True)

    assert capsys.readouterr().out == ""
    assert errors == ["Failed to fetch reference from missing"]


def test_cmd_from_rejects_unknown_output_type(monkeypatch):
    """Test an unsupported output type fails after a successful lookup."""

    async def fake_from_identifier(identifier):
        return _Reference(identifier)

    monkeypatch.setattr(cli, "async_from_identifier", fake_from_identifier)
    with pytest.raises(ValueError, match="Unknown output type: yaml"):
        cli.cmd_from(IDENTIFIER=["item"], output_type="yaml")


def test_cmd_from_rejects_unknown_default_extension():
    """Test unsupported default-file extensions are rejected."""
    with pytest.raises(ValueError, match="Unknown output type: yaml"):
        cli.cmd_from(IDENTIFIER=[], output=0, output_type="yaml")


def test_main_parses_and_dispatches(monkeypatch):
    """Test the top-level entry point dispatches parsed CLI arguments."""
    received = {}

    def fake_cmd_from(**kwargs):
        received.update(kwargs)

    monkeypatch.setattr(cli, "cmd_from", fake_cmd_from)
    monkeypatch.setattr(sys, "argv", ["wenxian", "from", "identifier"])
    cli.main()

    assert received["IDENTIFIER"] == ["identifier"]
    assert received["output"] is None
    assert received["output_type"] == "bibtex"
