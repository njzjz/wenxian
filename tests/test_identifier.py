"""Tests for the identifier module."""

from __future__ import annotations

import pytest

from wenxian.identifier import Identifier, get_identifier_type


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("10.1063/5.0155600", Identifier.DOI),
        ("37526163", Identifier.PMID),
        ("2304.09409", Identifier.ARXIV),
    ],
)
def test_get_identifier_type(identifier, expected):
    """Test get_identifier_type()."""
    assert get_identifier_type(identifier) == expected
