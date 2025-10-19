"""Test command line interface."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

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


def test_cli_from_to_default_file():
    """Test wenxian from DOI to the default file."""
    case = TEST_CASES[0]
    with tempfile.TemporaryDirectory() as tmpdirname:
        subprocess.check_call(
            [sys.executable, "-m", "wenxian", "from", case.reference.doi, "-o"],
            text=True,
            cwd=tmpdirname,
        )
        with open(Path(tmpdirname) / (case.reference.key + ".bib")) as f:
            # The default file is references.bib
            assert f.read().strip() == case.expected_bibtex.strip()


def test_cli_from_to_stdout_markdown():
    """Test wenxian from DOI to stdout."""
    case = TEST_CASES[0]
    out = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "wenxian",
            "from",
            case.reference.doi,
            "--type",
            "markdown",
        ],
        text=True,
    )
    assert out.strip() == case.expected_markdown.strip()


def test_cli_from_to_file_markdown():
    """Test wenxian from DOI to a certain file."""
    case = TEST_CASES[0]
    with tempfile.NamedTemporaryFile("w+") as f:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "wenxian",
                "from",
                case.reference.doi,
                "-o",
                f.name,
                "--type",
                "markdown",
            ],
            text=True,
        )
        f.seek(0)
        assert f.read().strip() == case.expected_markdown.strip()


def test_cli_from_to_default_file_markdown():
    """Test wenxian from DOI to the default file."""
    case = TEST_CASES[0]
    with tempfile.TemporaryDirectory() as tmpdirname:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "wenxian",
                "from",
                case.reference.doi,
                "-o",
                "--type",
                "markdown",
            ],
            text=True,
            cwd=tmpdirname,
        )
        with open(Path(tmpdirname) / (case.reference.key + ".md")) as f:
            # The default file is references.md
            assert f.read().strip() == case.expected_markdown.strip()


def test_cli_from_to_stdout_text():
    """Test wenxian from DOI to stdout."""
    case = TEST_CASES[0]
    out = subprocess.check_output(
        [
            sys.executable,
            "-m",
            "wenxian",
            "from",
            case.reference.doi,
            "--type",
            "text",
        ],
        text=True,
    )
    assert out.strip() == case.expected_text.strip()


def test_cli_from_to_file_text():
    """Test wenxian from DOI to a certain file."""
    case = TEST_CASES[0]
    with tempfile.NamedTemporaryFile("w+") as f:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "wenxian",
                "from",
                case.reference.doi,
                "-o",
                f.name,
                "--type",
                "text",
            ],
            text=True,
        )
        f.seek(0)
        assert f.read().strip() == case.expected_text.strip()


def test_cli_from_to_default_file_text():
    """Test wenxian from DOI to the default file."""
    case = TEST_CASES[0]
    with tempfile.TemporaryDirectory() as tmpdirname:
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "wenxian",
                "from",
                case.reference.doi,
                "-o",
                "--type",
                "text",
            ],
            text=True,
            cwd=tmpdirname,
        )
        with open(Path(tmpdirname) / (case.reference.key + ".txt")) as f:
            # The default file is references.txt
            assert f.read().strip() == case.expected_text.strip()


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
