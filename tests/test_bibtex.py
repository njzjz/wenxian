"""Tests for generating BibTeX entries from references."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from .cases import TEST_CASES

if TYPE_CHECKING:
    from wenxian.reference import Reference


@pytest.mark.parametrize(
    "reference, expected", [(cc.reference, cc.expected_bibtex) for cc in TEST_CASES]
)
def test_bibtex(reference: Reference, expected):
    """Test generating BibTeX entries from references."""
    assert reference.bibtex.strip() == expected
