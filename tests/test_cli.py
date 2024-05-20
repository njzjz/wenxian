"""Test command line interface."""

from __future__ import annotations

import subprocess
import sys
import tempfile

from .cases import TEST_CASES


def test_cli_from_to_stdout():
    """Test wenxian from DOI to stdout."""
    reference, bibtex = TEST_CASES[0]
    out = subprocess.check_output(
        [sys.executable, "-m", "wenxian", "from", reference.doi], text=True
    )
    assert out.strip() == bibtex.strip()


def test_cli_from_to_file():
    """Test wenxian from DOI to a certain file."""
    reference, bibtex = TEST_CASES[0]
    with tempfile.NamedTemporaryFile("w+") as f:
        subprocess.check_call(
            [sys.executable, "-m", "wenxian", "from", reference.doi, "-o", f.name],
            text=True,
        )
        f.seek(0)
        assert f.read().strip() == bibtex.strip()
