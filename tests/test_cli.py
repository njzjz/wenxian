"""Test command line interface."""

from __future__ import annotations

import subprocess
import sys
import tempfile

from .cases import TEST_CASES


def test_cli_from_to_stdout():
    """Test wenxian from DOI to stdout."""
    case = TEST_CASES[0]
    out = subprocess.check_output(
        [sys.executable, "-m", "wenxian", "from", case.reference.doi], text=True
    )
    assert out.strip() == case.expected_bibtex.strip()


def test_cli_from_to_file():
    """Test wenxian from DOI to a certain file."""
    case = TEST_CASES[0]
    with tempfile.NamedTemporaryFile("w+") as f:
        subprocess.check_call(
            [sys.executable, "-m", "wenxian", "from", case.reference.doi, "-o", f.name],
            text=True,
        )
        f.seek(0)
        assert f.read().strip() == case.expected_bibtex.strip()


def test_cli_ignore_errors():
    """Test wenxian from DOI to stdout."""
    # expected success
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "wenxian",
            "from",
            "this_is_not_an_identifier",
            "--ignore-errors",
        ],
        text=True,
    )
    # expected failure
    retcode = subprocess.call(
        [sys.executable, "-m", "wenxian", "from", "this_is_not_an_identifier"],
        text=True,
    )
    assert retcode == 1
