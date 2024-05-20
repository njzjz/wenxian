"""Nox configuration file."""

from __future__ import annotations

import nox


@nox.session
def tests(session: nox.Session) -> None:
    """Run test suite with pytest."""
    session.create_tmp()
    session.install("-e.[test]")
    session.run(
        "pytest",
        "--cov",
        "--cov-config",
        "pyproject.toml",
    )
