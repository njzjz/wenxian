"""Test cases for the from_identifier function."""

from __future__ import annotations

import pytest

from wenxian.from_identifier import from_identifier

from .cases import TEST_CASES


@pytest.mark.parametrize(
    "identifier, expected",
    [
        *[
            pytest.param(
                test_case.reference.doi,
                test_case.reference,
                marks=pytest.mark.skip(reason=test_case.skip_reason)
                if test_case.skip_reason
                else (),
            )
            for test_case in TEST_CASES
        ],
        *[
            # from_identifier accept str
            pytest.param(
                str(test_case.pmid),
                test_case.reference,
                marks=pytest.mark.skip(reason=test_case.skip_reason)
                if test_case.skip_reason
                else (),
            )
            for test_case in TEST_CASES
            if test_case.pmid is not None
        ],
        *[
            pytest.param(
                test_case.arxiv,
                test_case.reference,
                marks=pytest.mark.skip(reason=test_case.skip_reason)
                if test_case.skip_reason
                else (),
            )
            for test_case in TEST_CASES
            if test_case.arxiv is not None
        ],
    ],
)
def test_from_identifier(identifier, expected):
    """Test from_identifier function."""
    assert from_identifier(identifier) == expected
