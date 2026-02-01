"""Test cases for the from_identifier function."""

from __future__ import annotations

import pytest

from wenxian.from_identifier import from_identifier

from .cases import TEST_CASES, ReferenceCase


def _create_test_param(test_case: ReferenceCase, identifier: str):
    """Create a pytest.param with skip marks if needed."""
    return pytest.param(
        identifier,
        test_case.reference,
        marks=pytest.mark.skip(reason=test_case.skip_reason)
        if test_case.skip_reason
        else (),
    )


@pytest.mark.parametrize(
    "identifier, expected",
    [
        *[
            _create_test_param(test_case, test_case.reference.doi)
            for test_case in TEST_CASES
        ],
        *[
            # from_identifier accept str
            _create_test_param(test_case, str(test_case.pmid))
            for test_case in TEST_CASES
            if test_case.pmid is not None
        ],
        *[
            _create_test_param(test_case, test_case.arxiv)
            for test_case in TEST_CASES
            if test_case.arxiv is not None
        ],
    ],
)
def test_from_identifier(identifier, expected):
    """Test from_identifier function."""
    assert from_identifier(identifier) == expected
