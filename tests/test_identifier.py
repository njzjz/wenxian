"""Tests for the identifier module."""

from __future__ import annotations

import pytest

from wenxian.identifier import Identifier, get_identifier_type


@pytest.mark.parametrize(
    "identifier, expected",
    [
        ("10.1063/5.0155600", Identifier.DOI),
        ("37526163", Identifier.PMID),
        ("1234567", Identifier.PMID),
        ("1", Identifier.PMID),
        ("2304.09409", Identifier.ARXIV),
        ("2304.09409v2", Identifier.ARXIV),
        ("hep-th/9901001", Identifier.ARXIV),
        ("hep-th/9901001v2", Identifier.ARXIV),
        ("math.GT/0309136", Identifier.ARXIV),
        ("Deep residual learning for image recognition", Identifier.TITLE),
    ],
)
def test_get_identifier_type(identifier, expected):
    """Test get_identifier_type()."""
    assert get_identifier_type(identifier) == expected


@pytest.mark.parametrize(
    "identifier",
    [
        "10.1063/5.0155600 trailing",
        "2304.09409 trailing",
        "hep-th/9901001 trailing",
        "123456789",
    ],
)
def test_get_identifier_type_rejects_malformed_identifiers(identifier):
    """Test malformed identifier-like strings are not accepted by prefix."""
    assert get_identifier_type(identifier) is None
