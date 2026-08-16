"""Regression tests for reference type merging."""

from __future__ import annotations

from wenxian.reference import BibtexType, Reference


def test_empty_accumulator_adopts_source_type():
    """Test an empty merge accumulator adopts the first real source type."""
    merged = Reference() | Reference(title="Chapter", type=BibtexType.inbook)
    assert merged.type is BibtexType.inbook


def test_article_priority_is_not_lost_to_falsy_enum_value():
    """Test a higher-priority article type is preserved during merge."""
    primary = Reference(title="Article", type=BibtexType.article)
    lower_priority = Reference(journal="Book", type=BibtexType.inbook)
    assert (primary | lower_priority).type is BibtexType.article


def test_non_article_priority_is_preserved():
    """Test an existing non-article type also keeps source priority."""
    primary = Reference(title="Chapter", type=BibtexType.inbook)
    lower_priority = Reference(journal="Journal", type=BibtexType.article)
    assert (primary | lower_priority).type is BibtexType.inbook
