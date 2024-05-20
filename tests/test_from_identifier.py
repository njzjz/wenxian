"""Test cases for the from_identifier function."""

from __future__ import annotations

import pytest

from wenxian.from_identifier import from_identifier

from .cases import TEST_CASES


@pytest.mark.parametrize(
    "identifier, expected",
    [(test_case[0].doi, test_case[0]) for test_case in TEST_CASES],
)
def test_from_identifier(identifier, expected):
    """Test from_identifier function."""
    assert from_identifier(identifier) == expected
