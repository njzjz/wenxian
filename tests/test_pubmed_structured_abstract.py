"""Regression tests for PubMed structured abstracts."""

from __future__ import annotations

from wenxian.feeder.pubmed import Pubmed


def _xml(abstract: str) -> bytes:
    return f"""
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <Article>
        <ArticleTitle>Example.</ArticleTitle>
        {abstract}
        <Journal>
          <Title>Example Journal</Title>
          <JournalIssue><PubDate><Year>2024</Year></PubDate></JournalIssue>
        </Journal>
      </Article>
    </MedlineCitation>
    <PubmedData />
  </PubmedArticle>
</PubmedArticleSet>
""".encode()


def test_structured_abstract_keeps_all_sections():
    """Test all sibling AbstractText sections are preserved in document order."""
    reference = Pubmed()._from_content(
        _xml(
            """
        <Abstract>
          <AbstractText Label="BACKGROUND">Background text.</AbstractText>
          <AbstractText Label="METHODS">Methods <i>nested</i> text.</AbstractText>
          <AbstractText Label="RESULTS">Results text.</AbstractText>
        </Abstract>
        """
        )
    )
    assert reference is not None
    assert reference.annote == "Background text. Methods nested text. Results text."


def test_single_abstract_section_is_unchanged():
    """Test a conventional single-section abstract retains its content."""
    reference = Pubmed()._from_content(
        _xml("<Abstract><AbstractText>Only section.</AbstractText></Abstract>")
    )
    assert reference is not None
    assert reference.annote == "Only section."


def test_missing_abstract_remains_none():
    """Test records without an abstract still produce no abstract value."""
    reference = Pubmed()._from_content(_xml(""))
    assert reference is not None
    assert reference.annote is None
