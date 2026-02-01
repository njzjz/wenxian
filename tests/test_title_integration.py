"""Integration tests for title search with real API calls."""

from __future__ import annotations

import pytest

from wenxian.from_identifier import from_title


@pytest.mark.parametrize(
    "title",
    [
        "Attention is all you need",
        "Deep residual learning for image recognition",
        "ImageNet classification with deep convolutional neural networks",
    ],
)
def test_from_title_real_api(title):
    """Test title search with real API calls."""
    result = from_title(title)

    # Should return a valid reference
    assert result is not None
    assert not result.is_empty()

    # Should have a title
    assert result.title is not None

    # Title should be reasonably similar (case-insensitive comparison)
    assert (
        title.lower() in result.title.lower() or result.title.lower() in title.lower()
    )
